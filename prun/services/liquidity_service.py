# mypy: ignore-errors
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import json
from sqlmodel import select, func

from prun.interface import LiquidityRepositoryInterface
from prun.models import (
    Commitment,
    WalletSnapshot,
    ProjectionBucket,
    RawEvent,
    ReconciliationEvent,
    Transaction,
)
from prun.config import LIQUIDITY_CONFIG

logger = logging.getLogger(__name__)


class LiquidityService:
    """Service for handling liquidity operations."""

    def __init__(self, liquidity_repository: LiquidityRepositoryInterface):
        """Initialize the service.

        Args:
            repository: Repository for database operations
        """
        self.liquidity_repository = liquidity_repository
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate the liquidity configuration."""
        required_keys = [
            "safety_buffer_percent",
            "min_safety_buffer",
            "variance_tolerance",
        ]
        for key in required_keys:
            if key not in LIQUIDITY_CONFIG:
                raise ValueError(f"Missing required configuration key: {key}")

    def get_current_balance(self) -> float:
        """Get the current wallet balance.

        Returns:
            Current wallet balance

        Raises:
            Exception: If there's an error retrieving the balance
        """
        try:
            return self.liquidity_repository.get_current_balance()
        except Exception as e:
            logger.error(f"Error getting current balance: {str(e)}")
            raise

    def create_wallet_snapshot(
        self, balance: float, notes: Optional[str] = None
    ) -> None:
        """Create a new wallet snapshot.

        Args:
            balance: Current balance
            notes: Optional notes about the snapshot
        """
        self.liquidity_repository.create_wallet_snapshot(balance, notes)

    def calculate_safety_buffer(self, balance: float) -> float:
        """Calculate the safety buffer based on current balance.

        Args:
            balance: Current balance

        Returns:
            Safety buffer amount
        """
        return max(
            balance * LIQUIDITY_CONFIG["safety_buffer_percent"],
            LIQUIDITY_CONFIG["min_safety_buffer"],
        )

    def create_projection_bucket(
        self,
        start_ts: datetime,
        end_ts: datetime,
        balance_start: float,
        commitments: List[Commitment],
    ) -> ProjectionBucket:
        """Create a projection bucket for a time period.

        Args:
            start_ts: Start timestamp
            end_ts: End timestamp
            balance_start: Starting balance
            commitments: List of commitments in the period

        Returns:
            Projection bucket for the period
        """
        inflow = sum(c.amount for c in commitments if c.amount > 0)
        outflow = sum(abs(c.amount) for c in commitments if c.amount < 0)
        balance_end = balance_start + inflow - outflow

        return ProjectionBucket(
            start_ts=start_ts,
            end_ts=end_ts,
            inflow=inflow,
            outflow=outflow,
            balance_start=balance_start,
            balance_end=balance_end,
            is_negative=balance_end < 0,
        )

    def create_scenario(
        self,
        name: str,
        base_commitments: List[Commitment],
        modifications: List[Dict[str, Any]],
    ) -> List[Commitment]:
        """Create a what-if scenario by modifying base commitments.

        Args:
            name: Scenario name
            base_commitments: List of base commitments
            modifications: List of modifications to apply

        Returns:
            List of modified commitments for the scenario
        """
        scenario_commitments = []

        # Clone base commitments
        for commitment in base_commitments:
            scenario_commitment = Commitment(
                eta=commitment.eta,
                amount=commitment.amount,
                category=commitment.category,
                ref=commitment.ref,
                notes=commitment.notes,
                status="SCENARIO",
            )
            scenario_commitments.append(scenario_commitment)

        # Apply modifications
        for mod in modifications:
            if mod["type"] == "delay":
                for commitment in scenario_commitments:
                    if commitment.ref == mod["ref"]:
                        commitment.eta += timedelta(days=mod["days"])
            elif mod["type"] == "amount":
                for commitment in scenario_commitments:
                    if commitment.ref == mod["ref"]:
                        commitment.amount = mod["amount"]
            elif mod["type"] == "add":
                scenario_commitments.append(
                    Commitment(
                        eta=mod["eta"],
                        amount=mod["amount"],
                        category=mod["category"],
                        ref=mod["ref"],
                        notes=mod.get("notes"),
                        status="SCENARIO",
                    )
                )

        return scenario_commitments

    def compare_scenarios(
        self,
        base_scenario: List[Commitment],
        what_if_scenario: List[Commitment],
        days: int = 30,
    ) -> Dict[str, Any]:
        """Compare two scenarios and return the differences.

        Args:
            base_scenario: Base scenario commitments
            what_if_scenario: What-if scenario commitments
            days: Number of days to project

        Returns:
            Dictionary of scenario differences
        """
        base_buckets = self.generate_projection(base_scenario, days)
        what_if_buckets = self.generate_projection(what_if_scenario, days)

        return {
            "min_balance_diff": min(
                b2.balance_end - b1.balance_end
                for b1, b2 in zip(base_buckets, what_if_buckets)
            ),
            "total_inflow_diff": sum(
                b2.inflow - b1.inflow for b1, b2 in zip(base_buckets, what_if_buckets)
            ),
            "total_outflow_diff": sum(
                b2.outflow - b1.outflow for b1, b2 in zip(base_buckets, what_if_buckets)
            ),
            "negative_buckets_diff": sum(
                b2.is_negative - b1.is_negative
                for b1, b2 in zip(base_buckets, what_if_buckets)
            ),
        }

    def generate_projection(
        self, commitments: List[Commitment], days: int = 30
    ) -> List[ProjectionBucket]:
        """Generate a cash flow projection for the given commitments.

        Args:
            commitments: List of commitments
            days: Number of days to project

        Returns:
            List of projection buckets
        """
        buckets = []
        current_balance = self.get_current_balance()

        for i in range(days):
            start_ts = datetime.utcnow() + timedelta(days=i)
            end_ts = start_ts + timedelta(days=1)

            period_commitments = [c for c in commitments if start_ts <= c.eta < end_ts]

            bucket = self.create_projection_bucket(
                start_ts=start_ts,
                end_ts=end_ts,
                balance_start=current_balance,
                commitments=period_commitments,
            )

            buckets.append(bucket)
            current_balance = bucket.balance_end

        return buckets

    def record_raw_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Record a raw event for event sourcing.

        Args:
            event_type: Type of event
            data: Event data
        """
        self.liquidity_repository.create_raw_event(event_type, data)

    def process_raw_events(self) -> None:
        """Process unprocessed raw events."""
        try:
            events = self.liquidity_repository.get_unprocessed_events()
            for event in events:
                try:
                    data = json.loads(event.data)
                    self._process_event(event.event_type, data)
                    self.liquidity_repository.mark_event_processed(event.id)
                except Exception as e:
                    self.liquidity_repository.mark_event_error(event.id, str(e))
                    logger.error(f"Error processing event {event.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing raw events: {str(e)}")
            raise

    def _process_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Process a single event based on its type.

        Args:
            event_type: Type of event
            data: Event data
        """
        if event_type == "TRANSACTION":
            self._process_transaction(data)
        elif event_type == "COMMITMENT":
            self._process_commitment(data)
        elif event_type == "RECONCILIATION":
            self._process_reconciliation(data)

    def reconcile_commitments(self) -> None:
        """Reconcile pending commitments with actual transactions."""
        try:
            pending_commitments = self.liquidity_repository.get_pending_commitments()
            recent_transactions = self.liquidity_repository.get_recent_transactions(
                limit=100
            )

            for commitment in pending_commitments:
                for transaction in recent_transactions:
                    if self._is_match(commitment, transaction):
                        self._record_match(commitment, transaction)
                        break
                else:
                    if datetime.utcnow() > commitment.eta + timedelta(days=1):
                        self._record_late(commitment)
        except Exception as e:
            logger.error(f"Error reconciling commitments: {str(e)}")
            raise

    def _is_match(self, commitment: Commitment, transaction: Transaction) -> bool:
        """Check if a transaction matches a commitment.

        Args:
            commitment: Commitment to check
            transaction: Transaction to check

        Returns:
            True if the transaction matches the commitment
        """
        variance = abs(transaction.amount - commitment.amount) / abs(commitment.amount)
        if variance > LIQUIDITY_CONFIG["variance_tolerance"]:
            return False

        time_diff = abs((transaction.ts - commitment.eta).total_seconds())
        if time_diff > 3600:  # 1 hour tolerance
            return False

        if transaction.category != commitment.category:
            return False

        return True

    def _record_match(self, commitment: Commitment, transaction: Transaction) -> None:
        """Record a successful match between commitment and transaction.

        Args:
            commitment: Matched commitment
            transaction: Matching transaction
        """
        self.liquidity_repository.record_commitment_match(
            commitment_id=commitment.id,
            transaction_id=transaction.id,
            variance=transaction.amount - commitment.amount,
        )

    def _record_late(self, commitment: Commitment) -> None:
        """Record a late commitment.

        Args:
            commitment: Late commitment
        """
        self.liquidity_repository.record_late_commitment(commitment.id)

    def _record_variant(self, commitment: Commitment, transaction: Transaction) -> None:
        """Record a commitment with significant variance.

        Args:
            commitment: Variant commitment
            transaction: Matching transaction
        """
        self.liquidity_repository.record_variant_commitment(
            commitment_id=commitment.id,
            transaction_id=transaction.id,
            variance=transaction.amount - commitment.amount,
        )

    def _process_transaction(self, data: Dict[str, Any]) -> None:
        """Process a transaction event.

        Args:
            data: Transaction data

        Raises:
            ValueError: If required fields are missing
            Exception: If there's an error processing the transaction
        """
        try:
            required_fields = ["amount", "category", "ts"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            self.liquidity_repository.create_transaction(
                amount=data["amount"],
                category=data["category"],
                ts=data["ts"],
                notes=data.get("notes"),
            )
        except Exception as e:
            logger.error(f"Error processing transaction: {str(e)}")
            raise

    def _process_commitment(self, data: Dict[str, Any]) -> None:
        """Process a commitment event.

        Args:
            data: Commitment data

        Raises:
            ValueError: If required fields are missing
            Exception: If there's an error processing the commitment
        """
        try:
            required_fields = ["amount", "category", "eta"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            self.liquidity_repository.create_commitment(
                amount=data["amount"],
                category=data["category"],
                eta=data["eta"],
                ref=data.get("ref"),
                notes=data.get("notes"),
            )
        except Exception as e:
            logger.error(f"Error processing commitment: {str(e)}")
            raise

    def _process_reconciliation(self, data: Dict[str, Any]) -> None:
        """Process a reconciliation event.

        Args:
            data: Reconciliation data

        Raises:
            ValueError: If required fields are missing
            Exception: If there's an error processing the reconciliation
        """
        try:
            required_fields = ["commitment_id", "event_type"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            self.liquidity_repository.create_reconciliation_event(
                commitment_id=data["commitment_id"],
                event_type=data["event_type"],
                variance=data.get("variance"),
                notes=data.get("notes"),
            )
        except Exception as e:
            logger.error(f"Error processing reconciliation: {str(e)}")
            raise
