from hworkflow.v2.projects import VOCDet

git_repo = 'gourmets/experiments'
sheet_id = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
access_token = "aa8f2297d25b4dc6fd3d98411eb3ba53823c4f42"
secret_file = "credentials.json"
token_file = "token.pickle"
envs = {"REMOTE_DDIR": "gs://tensorflow-datasets/tfds"}

project = VOCDet("VOC-Detection", git_repo, sheet_id, access_token, secret_file, token_file,
                 sub_sheet="VOC", worker_id=1, **envs)
row = 40
project.fetch_code(row)
project.run_retry(row)