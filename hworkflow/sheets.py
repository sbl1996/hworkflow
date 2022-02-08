import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class GoogleSheet:
    scopes = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, spreadsheet_id, secret_file, token_file) -> None:
        self.service = self._init_service(secret_file, token_file)
        self.spreadsheet_id = spreadsheet_id

    def _init_service(self, secret_file, token_file, console=True):
        creds = None
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    secret_file, self.scopes)
                if console:
                    creds = flow.run_console()
                else:
                    creds = flow.run_local_server(port=0)
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        return build('sheets', 'v4', credentials=creds, cache_discovery=False)

    def read_values(self, ranges, sheet='Sheet1'):
        r"""
        Examples::
            >>> self.read_values('L121:M121')
            >>> ['79.17', '94.29']
            >>> self.read_values(['L121', 'M121'])
            >>> [['79.17'], ['94.29']]
            >>>
            >>> self.read_values(['K120', 'L120', "M120", "N120", "O120"])
            >>> [['78.44'], ['94.32'], ['2.3214'], ['29:45:46\n\n356.8'], []]
            >>> self.read_values("K120:O120")
            >>> ['78.44', '94.32', '2.3214', '29:45:46\n\n356.8'] # CAUTIONS
        """
        if isinstance(ranges, str):
            range_name = f'{sheet}!{ranges}'
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id, range=range_name).execute()
            values = result.get('values', [])[0]
        else:
            range_names = [f'{sheet}!{range}' for range in ranges]
            result = self.service.spreadsheets().values().batchGet(
                spreadsheetId=self.spreadsheet_id, ranges=range_names).execute()
            values = result.get('valueRanges', [])
            values = [v.get("values", [[]])[0] for v in values]
        return values

    def update_values(self, ranges, values, sheet='Sheet1'):
        r"""
        Examples::
            >>> self.update_values('K121:L121', ['79.17', '94.29'])
            >>>
            >>> self.update_values(['K121', 'L121'], [['79.17'], ['94.29']])
        """
        if isinstance(ranges, str):
            range_name = f'{sheet}!{ranges}'
            body = {
                'values': [values],
            }
            return self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id, range=range_name,
                valueInputOption="RAW", body=body).execute()
        else:
            range_names = [f'{sheet}!{range}' for range in ranges]
            data = [
                {"range": r, "values": [v]}
                for r, v in zip(range_names, values)
            ]
            body = {
                "valueInputOption": "RAW",
                "data": data,
            }
            return self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=self.spreadsheet_id, body=body).execute()


    def append_result(self, row, ranges, result, update_methods):
        r"""
        Examples::
            >>> result = ['80.22', '94.65', '2.6662', '14:50:13\n\n266.3', '5a2f14f']
            >>> update_methods = ['A', 'A', 'A', 'W', 'W']
                >>> self.append_result(118, ['K', 'L', 'M', 'N', 'O'], result)
            >>> seq
            2
        """
        assert len(ranges) == len(result) == len(update_methods)
        ranges = [f"{r}{row}" for r in ranges]
        results = self.read_values(ranges)
        results = update_results(results, result, update_methods)
        self.update_values(ranges, results)
        if 'A' not in update_methods:
            seq = 1
        else:
            i = update_methods.index('A')
            seq = len(results[0][i].split())
        return seq


def update_results(results, new_result, update_methods):
    r"""
    Examples::
        >>> results = [['80.30\n80.14'], ['94.68\n94.62'], ['2.6844\n2.6551'], ['14:49:28\n\n266.0'], []]
        >>> new_result = ['80.22', '94.65', '2.6662', '14:50:13\n\n266.3', '5a2f14f']
        >>> update_methods = ['A', 'A', 'A', 'W', 'W']
        >>> update_results(results, new_result, update_methods)
        [['80.30\n80.14\n80.22'], ['94.68\n94.62\n94.65'], ['2.6844\n2.6551\n2.6662'], ['14:50:13\n\n266.3'], ['5a2f14f']]
    """
    # noinspection PySimplifyBooleanCheck
    if results[0] == []:
        return [[r] for r in new_result]
    else:
        assert len(results) == len(new_result) == len(update_methods)
        updated = []
        for vs, v, m in zip(results, new_result, update_methods):
            if m == 'W':
                updated.append([v])
            elif m == 'A':
                updated.append(['\n'.join(vs[0].split('\n') + [v])])
            else:
                raise ValueError("Invalid update method: %s" % m)
        return updated