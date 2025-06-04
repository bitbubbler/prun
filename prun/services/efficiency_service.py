import logging

from prun.models import Building, Experts


logger = logging.getLogger(__name__)


class EfficiencyService:
    """
    Service for handling both expert and COGC program efficiency calculations.
    """

    # Expert constants
    EXPERT_BONUSES = [0.0306, 0.0696, 0.1248, 0.1974, 0.2840]
    EXPERT_DAYS = [10.00, 12.50, 57.57, 276.50, 915.10]
    MAX_EXPERTS_PER_INDUSTRY = 5
    MAX_EXPERTS_TOTAL = 6

    # COGC constants
    COGC_PROGRAMS = [
        "agriculture",
        "chemistry",
        "construction",
        "electronics",
        "food industry",
        "fuel refining",
        "manufacturing",
        "metallurgy",
        "resource extraction",
    ]
    COGC_BONUS = 0.25

    # Expert methods
    @classmethod
    def get_expert_efficiency(cls, experts: Experts, expertise: str) -> float:
        """
        Returns the total expert bonus multiplier for a given number of experts.
        For example, 3 experts returns 0.1248 (12.48%).
        If num_experts is 0, returns 0.0.
        """
        num_experts = experts.num_experts(expertise)
        if num_experts <= 0:
            return 0.0
        if num_experts > cls.MAX_EXPERTS_PER_INDUSTRY:
            logger.warning(
                f"num_experts {num_experts} is greater than MAX_EXPERTS_PER_INDUSTRY of {cls.MAX_EXPERTS_PER_INDUSTRY}"
            )
        num_experts = min(num_experts, cls.MAX_EXPERTS_PER_INDUSTRY)
        return cls.EXPERT_BONUSES[num_experts - 1]

    @classmethod
    def get_days_to_next_expert(cls, current_experts: int, num_buildings: int = 1) -> float:
        """
        Returns the days required to spawn the next expert, given the current number of experts
        and the number of buildings in the industry. If max experts reached, returns 0.
        """
        if current_experts >= cls.MAX_EXPERTS_PER_INDUSTRY:
            return 0.0
        return cls.EXPERT_DAYS[current_experts] / max(1, num_buildings)

    @classmethod
    def get_total_days_for_experts(cls, target_experts: int, num_buildings: int = 1) -> float:
        """
        Returns the total days required to reach a given number of experts from 0,
        given the number of buildings in the industry.
        """
        target_experts = min(target_experts, cls.MAX_EXPERTS_PER_INDUSTRY)
        total_days = 0.0
        for i in range(target_experts):
            total_days += cls.EXPERT_DAYS[i] / max(1, num_buildings)
        return total_days

    # COGC methods
    @classmethod
    def get_cogc_programs(cls):
        """Returns the list of valid COGC programs."""
        return cls.COGC_PROGRAMS

    @classmethod
    def is_valid_cogc_program(cls, program: str) -> bool:
        """Checks if the given program is a valid COGC program."""
        return program in cls.COGC_PROGRAMS

    @classmethod
    def get_cogc_efficiency(cls, building: Building, program: str | None = None) -> float:
        """
        Returns the efficiency percentage for a given COGC program.
        If the program is not valid, returns 0.0.
        """
        if program is None:
            return 0.0
        if not cls.is_valid_cogc_program(program):
            raise ValueError(f"Invalid program: {program}")
        if building.expertise.lower() == program:
            return cls.COGC_BONUS
        return 0.0
