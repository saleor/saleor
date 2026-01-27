from collections import defaultdict

from ....app.models import AppProblem
from ...core.dataloaders import DataLoader


class AppProblemsByAppIdLoader(DataLoader[int, list[AppProblem]]):
    context_key = "app_problems_by_app_id"

    def batch_load(self, keys):
        problems = AppProblem.objects.using(self.database_connection_name).filter(
            app_id__in=keys
        )
        problem_map = defaultdict(list)
        for problem in problems:
            problem_map[problem.app_id].append(problem)
        return [problem_map.get(app_id, []) for app_id in keys]
