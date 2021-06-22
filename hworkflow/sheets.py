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
        range_name = f'{sheet}!{ranges}'
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        return values

    def update_values(self, ranges, values, sheet='Sheet1'):
        range_name = f'{sheet}!{ranges}'
        body = {
            'values': values,
        }
        return self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id, range=range_name,
            valueInputOption="RAW", body=body).execute()


    def append_result(self, row, ranges, result, update_last=False):
        r"""
        Append result to the sheet row.

        Args:
          ranges: `[..., num_features]` unnormalized log probabilities
          result: non-negative scalar temperature

        Returns:
          Seq number

        Examples::
            >>> result = ['78.22', '93.99', '1.8062', '12:02:13\n\n358.6']
            >>> seq = sheet.append_result('K97:N97', result)
            >>> print(seq)
                97-2
        """
        range_min, range_max = ranges
        ranges = f"{range_min}{row}:{range_max}{row}"
        results = self.read_values(ranges)
        results = update_results(results, result, update_last)
        self.update_values(ranges, results)
        seq = len(results[0][0].split())
        return seq


def update_results(results, new_result, update_last):
    if not results:
        return [new_result]
    else:
        results = results[0]
        assert len(results) == len(new_result)
        if update_last:
            results = [
                '\n'.join(v.split('\n') + [new_v])
                for v, new_v in zip(results, new_result)
            ]
        else:
            results = [
                          '\n'.join(v.split('\n') + [new_v])
                          for v, new_v in zip(results[:-1], new_result[:-1])
                      ] + [results[-1]]
        return [results]