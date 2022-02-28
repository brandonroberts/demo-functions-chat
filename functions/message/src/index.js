const sdk = require('node-appwrite');
const fetch = require('node-fetch');
const { Headers, Request, Response } = require('node-fetch');

if (!globalThis.fetch) {
	globalThis.fetch = fetch;
	globalThis.Headers = Headers;
	globalThis.Request = Request;
	globalThis.Response = Response;
}

/*
  'req' variable has:
    'headers' - object with request headers
    'payload' - object with request body data
    'env' - object with environment variables

  'res' variable has:
    'send(text, status)' - function to return text response. Status code defaults to 200
    'json(obj, status)' - function to return JSON response. Status code defaults to 200

  If an error is thrown, a response with code 500 will be returned.
*/

module.exports = async function (req, res) {
	const client = new sdk.Client();

	// You can remove services you don't use
	let account = new sdk.Account(client);
	let avatars = new sdk.Avatars(client);
	let database = new sdk.Database(client);
	let functions = new sdk.Functions(client);
	let health = new sdk.Health(client);
	let locale = new sdk.Locale(client);
	let storage = new sdk.Storage(client);
	let teams = new sdk.Teams(client);
	let users = new sdk.Users(client);

	if (!req.env['APPWRITE_FUNCTION_ENDPOINT'] || !req.env['APPWRITE_FUNCTION_API_KEY']) {
		console.warn('Environment variables are not set. Function cannot use Appwrite SDK.');
	} else {
		client
			.setEndpoint(req.env['APPWRITE_FUNCTION_ENDPOINT'])
			.setProject(req.env['APPWRITE_FUNCTION_PROJECT_ID'])
			.setKey(req.env['APPWRITE_FUNCTION_API_KEY'])
			.setSelfSigned(true);
	}

	const { GiphyFetch } = require('@giphy/js-fetch-api');

	// use @giphy/js-fetch-api to fetch gifs, instantiate with your api key
	const gf = new GiphyFetch(req.env['GIPHY_API_KEY']);

	// parse event data
	const data = JSON.parse(req.env['APPWRITE_FUNCTION_EVENT_DATA']);

	// fetch gif based on message
	const gifs = await gf.search(data.message, { limit: 1 });

	const resp = {
		areDevelopersAwesome: true,
		eventData: data,
		giphyKey: req.env['GIPHY_API_KEY'],
		gif: gifs.data[0] ? gifs.data[0].images.downsized.url : ''
	};

	const collectionId = data.$collection;
	const documentId = data.$id;
	const { user, room, message, $read, $write } = data;
	const document = {
		user,
		room,
		message,
		meme: resp.gif
	};

	try {
		await database.updateDocument(collectionId, documentId, document, $read, $write);
		res.json({ success: true });
	} catch (e) {
		res.send(`Unable to update meme for message ${e}}`, 400);
	}
};
