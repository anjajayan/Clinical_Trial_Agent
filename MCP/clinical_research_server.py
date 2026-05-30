from mcp.server.fastmcp import FastMCP
import httpx
import asyncio



mcp = FastMCP("CLinicalTrialsgov", json_response=True)
sem = asyncio.Semaphore(3) 

# we get json response from clinical trials

async def call_ctg_api(condition: str):
    # A simple GET request to a public API
    end_point = 'https://clinicaltrials.gov/api/v2/studies'
    params = {'query.cond': condition}
    async with httpx.AsyncClient() as client:
        response = await client.get(end_point, params = params)

        if response.status_code == 200:
        # Output: 200
            result = []

            # Parsing JSON data
            data = response.json()
            for study in data['studies']: # a list?

                identification = study['protocolSection']['identificationModule']
                org = identification.get('organization', {})
                title = identification.get('briefTitle', "")

                status_module = study['protocolSection']['statusModule']

                description = study['protocolSection']['descriptionModule']

                eligiblity = study['protocolSection']['eligibilityModule']

                location = study['protocolSection']['contactsLocationsModule']
                result.append({
                    'organization': org,
                    'title': title,
                    'status': status_module,
                    'description': description,
                    'eligibility': eligiblity,
                    'location': location
                })
            return result
        else:
            return "Error: could not retrieve clinical trials data. The API request failed."
     
async def call_pubmed_id(id):
    endpoint = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi'
    params = {'db': 'pubmed', 'id': id , 'retmode': 'json'}
    
    async with sem:
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint, params=params)
            if response.status_code == 200:
                if response.json() is not None:
                    # fetch required fields
                    result = response.json().get('result', {}).get(id, "")
                    if result:
                        title = result.get('title', "")
                        journal = result.get('fulljournalname', "")
                        pub_date = result.get('pubdate', "")
                        rd = {'title': title, 
                            'journal': journal,
                            'published_date': pub_date}
                    else:
                        rd = "There is no content at this id."
                else:
                    rd = "There is no content at this id."
            else:
                rd = "Error: could not retrieve Pub Med data. The API request failed."
    return rd
        
async def call_pubmed_api(condition: str):
    # 2 time api call
    # Get list of uids
    endpoint = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
    params = {'db': 'pubmed', 'term': condition, 'retmode': 'json'}
    async with httpx.AsyncClient() as client:
        response = await client.get(endpoint, params=params)
        if response.status_code == 200:
            id_data = response.json().get('esearchresult', None)
            if id_data:
                ids = id_data.get('idlist')
                # build a list of coroutines
                # only 3 requests per second
                coroutines = [call_pubmed_id(id) for id in ids]
                # Unpack the list
                result = await asyncio.gather(*coroutines)
                return result
            else: 
                return "Error: There is no IDs with this request"
        else:
            return "Error: Could not find any information for this request."




@mcp.tool()
async def search_trials(condition: str):

    response = await call_ctg_api(condition)
    return response

@mcp.tool()
async def search_pubmed(condition: str):
    response = await call_pubmed_api(condition)
    return response


        
