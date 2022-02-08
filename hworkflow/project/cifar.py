from hworkflow.project.base import Project

class CIFAR(Project):
    _parse_script = "$hanser/tools/parse_cifar_log.py"
    # accs, losses, time
    _sheet_ranges = ["K", "L", "M"]
    _update_methods = ["A", "A", "W"]
    _commit_range = 'O'
    _dep_repo = "hanser"