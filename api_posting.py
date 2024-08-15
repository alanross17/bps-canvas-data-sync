import requests

def post_csv_to_api(file_path, token, canvas_url, account_id):
    """
    Post a CSV file to the Canvas API endpoint.

    Args:
        file_path (str): Path to the CSV file to be uploaded.
        token (str): Bearer token for authorization.
        canvas_url (str): Base URL of the Canvas instance.
        account_id (str): Account ID for the SIS import.

    Returns:
        Response object from the API request.
    """
    url = f"https://{canvas_url}/api/v1/accounts/{account_id}/sis_imports.json?import_type=instructure_csv"
    headers = {
        'Content-Type': 'text/csv',
        'Authorization': f'Bearer {token}'
    }
    with open(file_path, 'rb') as f:
        response = requests.post(url, headers=headers, data=f)
    return response