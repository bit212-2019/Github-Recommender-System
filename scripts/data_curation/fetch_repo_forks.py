import requests, json
from pymongo import MongoClient

client = MongoClient()
database = client['cf_project']
users = database['users']
userRepos = database['userRepos']
repoForks = database['repoForksSmall']

users_names = users.find(timeout = False).limit(1000)

response = None
globalCounter = 0

for user_document in users_names:
	document = userRepos.find({'user_id' : user_document['id']}).limit(1)
	if( document.count() == 0 ):
		globalCounter += 1
		print(globalCounter)
		continue
	document = document[0]
	count = 1
	response = requests.get(document['forks_url'] + "?page=1&per_page=100&client_id=84690af0552c9ed4357b&client_secret=288d95782c060102e5f251cd880a386feef1d835")
	# response can be empty which signifies that the repository may be forked and user has not contributed anything to the repositories
	lastPage = 0
	result = dict()
	ownerID = []
	ownerLogin = []
	result['repo_id'] = document['id']
	if( globalCounter % 100 == 0 ):
		print("Ratelimit Left : {0}").format(response.headers.get("x-ratelimit-remaining", None))
		if( response.headers.get("x-ratelimit-remaining", None) == '0' ):
			print("Ratelimit reached!!!!")
			break
	while( response.ok ):
		link = response.headers.get('link', None)
		if( link is not None ):
			values = link.split(",")
			if( 'rel="last"' in values[1] ):
				lastPage = int(values[1].split("?")[1].split("&")[0][5:])
		item = json.loads(response.text or response.content)
		if( len(item) != 0 ):
			for repo in item:
				ownerID.append(repo['owner']['id'])
				ownerLogin.append(repo['owner']['login'])
		if( link is not None and count < lastPage ):
			count += 1
			link = link.split(">")[0][1:]
			linkVal = link.split("?")
			newLink = linkVal[0] + "?" + linkVal[1].split("&")[0][:5] + str(count) + "&" + linkVal[1].split("&")[1] + "&" + linkVal[1].split("&")[2] + "&" + linkVal[1].split("&")[3]
			response = requests.get(newLink)
		else:
			result['user_id'] = ownerID
			result['login'] = ownerLogin
			repoForks.update(result, result, upsert = True)
			break
	print(globalCounter)
	globalCounter += 1

users_names.close()