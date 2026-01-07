
const getApiUrl = () => {
    return 'http://localhost:8000';
};

const apiUrlHandler = {
    toString: getApiUrl,
    valueOf: getApiUrl
};

const API_URL = new Proxy(apiUrlHandler, {
    get(target, prop) {
        if (prop === 'toString' || prop === 'valueOf' || prop === Symbol.toPrimitive) {
            return () => getApiUrl();
        }
        return getApiUrl()[prop];
    }
});

console.log(`URL: ${API_URL}`);
console.log(`Path: ${API_URL}/api/test`);
console.log('Type:', typeof API_URL);
