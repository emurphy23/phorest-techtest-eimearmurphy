import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output
import requests
from dash.exceptions import PreventUpdate
import json
from datetime import datetime, date

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])
app.title = "Phorest Salon Software"
server = app.server

navbar = html.Div([
    dbc.Navbar(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.Img(src='assets/phorest.png', height="30px")),
                        dbc.Col(dbc.NavbarBrand("Phorest Salon Software", className="ml-2")),
                    ],
                    align="center",
                    no_gutters=True,
                ),
                href="https://www.phorest.com/gb/",
            ),
        ],
        color="dark",
        dark=True,
    )
])

body = html.Div([
    html.Label('Select which you would like to search by', style={'font-weight': 'bold'}),
    dbc.RadioItems(
        id='search-type',
        options=[
            {'label': 'Email address', 'value': 'email'},
            {'label': 'Phone number', 'value': 'phone'}
        ],
        value='email'
    ),
    html.Div(id='display-selected-search'),
    html.Br(),
    dbc.Button("Submit", color="primary", id="submit-button"),
    html.Div(id='voucher-amount'),
    dbc.Button("Submit", color="primary", id="submit-amount-button", style={'display': 'none'}),
    html.Div(id='voucher-success'),
    html.Br(),
    html.Div(id="refresh")
],
    style={'position': 'relative', 'left': '20px', 'top': '2px'}
)

app.layout = html.Div([
    navbar,
    body
])


@app.callback(
    Output('display-selected-search', 'children'),
    Input('search-type', 'value'))
def set_client_search(search_type):
    if search_type == 'email':
        return dbc.Form([
            dbc.FormGroup(
                [
                    dbc.Label("Email: ", className="mr-2"),
                    dbc.Input(
                        type="email",
                        id="email",
                        placeholder="Enter email address",
                    ),
                ]
            ),
        ],
            inline=True
        )
    else:
        return dbc.Form([
            dbc.FormGroup(
                [
                    dbc.Label("Phone: ", className="mr-2"),
                    dbc.Input(
                        type="text",
                        id="phone-number",
                        placeholder="Enter phone number",
                    ),
                ]
            ),
        ],
            inline=True
        )


client_ids = []


@app.callback(Output('voucher-amount', 'children'),
              Output('submit-amount-button', 'style'),
              Input('submit-button', 'n_clicks'),
              Input('display-selected-search', 'children'),
              )
def get_client(n_clicks, search):
    client_ids.clear()
    if n_clicks is None:
        raise PreventUpdate

    if n_clicks is not None and search is not None:
        parameters = {}
        # get value of email or phone number
        if search['props']['children'][0]['props']['children'][1]['props']['id'] == 'email' and 'value' in \
                search['props']['children'][0]['props']['children'][1]['props']:
            parameters["email"] = (search['props']['children'][0]['props']['children'][1]['props']['value'])

        elif search['props']['children'][0]['props']['children'][1]['props']['id'] == 'phone-number' and 'value' in \
                search['props']['children'][0]['props']['children'][1]['props']:
            parameters["phone"] = (search['props']['children'][0]['props']['children'][1]['props']['value'])
        if parameters:
            response = requests.get(
                'https://api-gateway-dev.phorest.com/third-party-api-server/api/business/eTC3QY5W3p_HmGHezKfxJw'
                '/client?size=20',
                params=parameters, auth=('global/cloud@apiexamples.com', 'VMlRo/eh+Xd8M~l'))
            # if a search comes back with a result
            if response.json()['page']['totalElements'] > 0:
                clients = response.json()['_embedded']['clients']

                for c in clients:
                    c_id = c['clientId']
                    name = c['firstName'] + " " + c['lastName']
                    email = c['email']
                    client_ids.append(c_id)
                    return dbc.FormGroup(
                        [
                            dbc.Label(f"Client ID: {c_id}: {name}, ({email}) "),
                            html.Br(),
                            dbc.Label(f"Input voucher amount (€)", style={'font-weight': 'bold'}),
                            dbc.Input(placeholder="Enter voucher amount", type="number", step=0.01,
                                      style={'width': '50%'})
                        ]
                    ), {'display': 'block'}
            else:
                return dbc.Alert("There are no matches", color="danger", dismissable=True, style={'width': '400px'}), {
                    'display': 'none'}
        else:
            return dbc.Alert("There are no matches", color="danger", dismissable=True, style={'width': '400px'}), {
                'display': 'none'}


now = datetime.now()


# function to calculate expiry date based on issue date
def addYears(d, years):
    try:
        # Return same day of the current year
        return d.replace(year=d.year + years)
    except ValueError:
        # If not same day, it will return other
        return d + (date(d.year + years, 1, 1) - date(d.year, 1, 1))


def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=4)
    return text


@app.callback(Output('voucher-success', 'children'),
              Output('refresh', 'children'),
              Input('submit-amount-button', 'n_clicks'),
              Input('voucher-amount', 'children'))
def create_voucher(n_clicks, amount):
    if n_clicks is not None and amount is not None and 'value' in amount['props']['children'][3]['props']:
        for client in client_ids:
            headers = {
                'Content-Type': 'application/json',
                'Accept': '*/*'
            }
            voucher_params = {"creatingBranchId": "SE-J0emUgQnya14mOGdQSw",
                              "expiryDate": addYears(now, 1).strftime("%Y-%m-%dT%H:%M:%S"),
                              "issueDate": now.strftime("%Y-%m-%dT%H:%M:%S"),
                              "originalBalance": amount['props']['children'][3]['props']['value'],
                              "clientId": client
                              }

            post_voucher = requests.post(
                'https://api-gateway-dev.phorest.com/third-party-api-server/api/business/eTC3QY5W3p_HmGHezKfxJw/voucher',
                json=voucher_params, headers=headers, auth=('global/cloud@apiexamples.com', 'VMlRo/eh+Xd8M~l'))

            card = dbc.Card(
                [
                    dbc.CardHeader(f"Serial Number: {post_voucher.json()['serialNumber']}"),
                    dbc.CardBody(
                        [
                            html.H5(f"Voucher Amount: €{post_voucher.json()['originalBalance']}",
                                    className="card-title"),
                            html.P(f"Issue Date: {post_voucher.json()['issueDate']}", className="card-text"),
                            html.P(f"Expiry Date: {post_voucher.json()['expiryDate']}", className="card-text"),
                        ]
                    ),

                ],
                style={"width": "15rem"},
                color="secondary",
                outline=True
            )
            return [html.Br(), dbc.Alert(
                f"A voucher for €{voucher_params['originalBalance']} for Client with ID '{client}' has been created successfully!",
                color="success", dismissable=True, style={'width': '700px'}), card], html.A(
                dbc.Button('Search Again', size="lg", outline=True, color="primary", className="mr-1"), href='/')
    else:
        raise PreventUpdate


if __name__ == '__main__':
    app.run_server(debug=True)
