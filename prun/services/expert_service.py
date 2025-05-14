import logging

logger = logging.getLogger(__name__)


class ExpertService:
    """
    Service for handling expert efficiency and spawn rate calculations.
    """

    # Expert bonuses for 1-5 experts (as decimal multipliers)
    EXPERT_BONUSES = [0.0306, 0.0696, 0.1248, 0.1974, 0.2840]
    # Days required for each expert (1-5), for a single building at 100% efficiency
    EXPERT_DAYS = [10.00, 12.50, 57.57, 276.50, 915.10]
    MAX_EXPERTS_PER_INDUSTRY = 5
    MAX_EXPERTS_TOTAL = 6

    def get_expert_efficiency(self, num_experts: int) -> float:
        """
        Returns the total expert bonus multiplier for a given number of experts.
        For example, 3 experts returns 0.1248 (12.48%).
        If num_experts is 0, returns 0.0.
        """
        if num_experts <= 0:
            return 0.0
        if num_experts > self.MAX_EXPERTS_PER_INDUSTRY:
            logger.warning(
                f"num_experts {num_experts} is greater than MAX_EXPERTS_PER_INDUSTRY of {self.MAX_EXPERTS_PER_INDUSTRY}"
            )
        num_experts = min(num_experts, self.MAX_EXPERTS_PER_INDUSTRY)
        return self.EXPERT_BONUSES[num_experts - 1]

    def get_days_to_next_expert(
        self, current_experts: int, num_buildings: int = 1
    ) -> float:
        """
        Returns the days required to spawn the next expert, given the current number of experts
        and the number of buildings in the industry. If max experts reached, returns 0.
        """
        if current_experts >= self.MAX_EXPERTS_PER_INDUSTRY:
            return 0.0
        # Days required for the next expert, divided by number of buildings
        return self.EXPERT_DAYS[current_experts] / max(1, num_buildings)

    def get_total_days_for_experts(
        self, target_experts: int, num_buildings: int = 1
    ) -> float:
        """
        Returns the total days required to reach a given number of experts from 0,
        given the number of buildings in the industry.
        """
        target_experts = min(target_experts, self.MAX_EXPERTS_PER_INDUSTRY)
        total_days = 0.0
        for i in range(target_experts):
            total_days += self.EXPERT_DAYS[i] / max(1, num_buildings)
        return total_days
