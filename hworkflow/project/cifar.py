from hworkflow.project.base import Project

class CIFAR(Project):
    _parse_script = "hanser/tools/parse_cifar_log.py"
    _sheet_range = ('K', 'M')
    _sheet_update_last = False