from hworkflow.v2.projects import CIFAR

git_repo = 'gourmets/experiments'
sheet_id = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
access_token = "aa8f2297d25b4dc6fd3d98411eb3ba53823c4f42"
secret_file = "credentials.json"
token_file = "token.pickle"

project = CIFAR("CIFAR10-TensorFlow", git_repo, sheet_id, access_token, secret_file, token_file, worker_id=1)

for row in [137, 138]:
    project.fetch_code(row)
    for i in range(5):
        project.run_retry(row)