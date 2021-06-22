from hworkflow.project.base import Project

class ImageNet(Project):
    _parse_script = "hanser/tools/parse_imagenet_log.py"
    _sheet_range = ('K', 'N')
    _sheet_update_last = False
    _suffix1 = False

    def parse_log(self, log_file):
        result = super().parse_log(log_file)
        result = result[:-2] + [result[-2] + "\n\n" + result[-1]]
        return result