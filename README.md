## Netfile Connect2 Swagger API

### Endpoint to get list of all form IDs
https://netfile.com:443/Connect2/api/public/list/form/types

Takes no arguments

Returns a list of forms and their IDs, as JSON, like
```json
{
  "items": [
    {
      "id": 245,
      "name": "FPPC 700",
      "description": "FPPC Form 700 Statement of Economic Interests (2002-2003)"
    }
  ]
}
```

### Endpoint to get a list of filings by form ID
POST https://netfile.com:443/Connect2/api/public/list/filing

Takes body like
```json
{
  "AID": "coak", // Oakland's unique name
  "Application": "",
  "CurrentPageIndex": "<int>",
  "Form": "254", // id of Form 700 yrs 2018-2019
  "PageSize": "<int>"
}
```

Returns a list of filings for the form ID, like
```json
{
  "filings": [
    {
      "id": "182305528", // pass this to /public/efile/{filingID}
      "agency": 13,
      "isEfiled": true,
      "hasImage": true,
      "filingDate": "2019-08-12T17:20:55.0000000-07:00",
      "title": "FPPC Form 700 (1/1/2018 - 12/31/2018)",
      "form": 254,
      "filerName": "Brooks, Desley",
      "filerLocalId": "COAK-151463",
      "filerStateId": "",
      "amendmentSequenceNumber": 0,
      "amendedFilingId": null
    },
  ],
  "responseStatus": null,
  "totalMatchingCount": 926,
  "totalMatchingPages": 10
}
```

### Endpoint to get a filing by filing ID
GET https://netfile.com:443/Connect2/api/public/efile/{filingId}

Returns zipped XML
