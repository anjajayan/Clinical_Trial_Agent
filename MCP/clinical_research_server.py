from mcp.server.fastmcp import FastMCP
import httpx
import asyncio



mcp = FastMCP("CLinicalTrialsgov", json_response=True)
sem = asyncio.Semaphore(3) 

# we get json response from clinical trials

async def call_ctg_api(condition: str):
    """
    Fetch clinical trial studies from ClinicalTrials.gov for a given condition.

    Args:
        condition: The medical condition or disease to search for.

    Returns:
        A list of dicts containing organization, title, status, eligibility,
        and location for up to 3 matching studies, or an error string on failure.
    """
    end_point = 'https://clinicaltrials.gov/api/v2/studies'
    params = {'query.cond': condition, 'pageSize': 3}
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

                eligiblity = study['protocolSection']['eligibilityModule'].get("eligibilityCriteria")

                location = study['protocolSection'].get('contactsLocationsModule', "")
                result.append({
                    'organization': org,
                    'title': title,
                    'status': status_module,
                    # 'description': description, # reducing tokens due to high cost
                    'eligibility': eligiblity,
                    'location': location
                })
            return result
        else:
            return "Error: could not retrieve clinical trials data. The API request failed."
     
async def call_pubmed_id(id):
    """
    Retrieve a single PubMed article summary by its ID.

    Uses a semaphore to limit concurrent requests to 3 at a time, respecting
    the NCBI rate limit.

    Args:
        id: The PubMed article ID (UID) to fetch.

    Returns:
        A dict with 'title', 'journal', and 'published_date' fields,
        a message string if no content is found, or an error string on failure.
    """
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
    """
    Search PubMed for articles related to a given condition.

    Makes two sequential API calls: first to retrieve a list of article IDs
    via the esearch endpoint, then fetches summaries for each ID concurrently
    using call_pubmed_id.

    Args:
        condition: The medical condition or search term to query PubMed with.

    Returns:
        A list of article summary dicts (title, journal, published_date),
        or an error string if the search or ID retrieval fails.
    """
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
    """
    MCP tool to search for clinical trials matching a given condition.

    Args:
        condition: The medical condition or disease to search for.

    Returns:
        A list of matching clinical trial summaries from ClinicalTrials.gov.
    """
    response = await call_ctg_api(condition)
    return response

@mcp.tool()
async def search_pubmed(condition: str):
    """
    MCP tool to search PubMed for research articles on a given condition.

    Args:
        condition: The medical condition or search term to query PubMed with.

    Returns:
        A list of article summaries (title, journal, published_date) from PubMed.
    """
    response = await call_pubmed_api(condition)
    return response

if __name__ == "__main__":
    mcp.run()


        
