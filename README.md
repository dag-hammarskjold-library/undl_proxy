# undl_proxy
Proxy app to UNDL searches

# Motivation

Users often need to embed metadata from searches performed on the 
United Nation Digital Library site into their own app, but do
not want to deal with MARCXML.

This application accepts a url from the United Nations Digital
Library and allows the user to choose what metadata fields to
display in either JSON or XML.

# Typical Use-Case

A user goes to the UNDL and enters the following (advanced) search:
symbol:'2017' AND (title:congo OR title:burundi)

This returns 48 records including Security Council resolutions, drafts, votes, letters and the like.  
The user would like to embed this information in a web report.

By copying and pasting:

https://digitallibrary.un.org/search?ln=en&p=symbol%3A%272017%27+AND+(title%3Acongo+OR+title%3Aburundi)&f=&c=Resource+Type&c=UN+Bodies&fti=0&sf=&so=d&rg=10&sc=0

into the `UNDL URL` textarea of this application, the app retrieves metadata from the UNDL and 
they can choose between JSON and XML representations associated to the items returned by
the search.

E.g. clicking on `XML` shows: 

```xml
<record>
<agenda/>
<author/>
<authors/>
<document_symbol/>
<electronic_locations/>
<imprint/>
<notes/>
<publisher/>
<pubyear/>
<related_documents>
<related_document>S/2017/993</related_document>
</related_documents>
<subjects/>
<summary/>
<title>
Security Council resolution 2389 (2017) [on implementation of the Peace, Security and Cooperation Framework for the Democratic Republic of the Congo and the Region]
</title>
<voting_record>
<vote>001 R BOL Y BOLIVIA (PLURINATIONAL STATE OF)</vote>
<vote>002 P CHN Y CHINA</vote>
<vote>003 R EGY Y EGYPT</vote>
<vote>004 R ETH Y ETHIOPIA</vote>
<vote>005 P FRA Y FRANCE</vote>
<vote>006 R ITA Y ITALY</vote>
<vote>007 R JPN Y JAPAN</vote>
<vote>008 R KAZ Y KAZAKHSTAN</vote>
<vote>009 P RUS Y RUSSIAN FEDERATION</vote>
<vote>010 R SEN Y SENEGAL</vote>
<vote>011 R SWE Y SWEDEN</vote>
<vote>012 R UKR Y UKRAINE</vote>
<vote>013 P GBR Y UNITED KINGDOM</vote>
<vote>014 P USA Y UNITED STATES</vote>
<vote>015 R URY Y URUGUAY</vote>
</voting_record>
</record>
```

as the first record returned (a vote).

This process makes it much easier to embed metadata into a report or simply link to the metadata's JSON
or XML representation for use in a web page.

Another Example:

User is searching UNDL for Voting Data -- https://digitallibrary.un.org/search?ln=en&cc=Voting+Data

This returns over 20,000 records -- but if the user is a little more specific -- and searches for 
voting data on Iran, most recent votes first they get 75 records.

https://digitallibrary.un.org/search?ln=en&cc=Voting+Data&p=iran&f=&rm=&ln=en&fti=0&sf=latest+first&so=d&rg=10&sc=0&c=Voting+Data&c=&of=hb

Now it is easy for this proxy app to parse through those 75 records and present all of the 
metadata.

    ```json
    [
      {
        "related_documents": {
          "A/72/439/Add.3": "http://dag.un.org/docs/A/72/439/Add.3",
          "A/C.3/72/L.41": "http://dag.un.org/docs/A/C.3/72/L.41"
        },
        "title": "Situation of human rights in the Islamic Republic of Iran : resolution /",
        "voting_record": [
          "1 AFG N AFGHANISTAN",
          "2 ALB Y ALBANIA",
          "3 DZA A ALGERIA",
          "4 AND Y ANDORRA",
          "5 AGO A ANGOLA",
          "6 ATG A ANTIGUA AND BARBUDA",
          "7 ARG Y ARGENTINA",
          "8 ARM N ARMENIA",
          "9 AUS Y AUSTRALIA",
          . . .
    ```
Here, any report or web application that can read JSON can easily parse all the results and 
present them in a human-readable form.


# Keeping data fresh

With the example above, a user may want to get the latest voting data.  With any search, 
new documents may have been published and made available on the UNDL site.

To get the latest data from the UNDL this proxy app offers a `Search Metadata` link that gives
a button `refresh JSON` and a button `refresh XML`.  Clicking refresh JSON gives a 
url similar to : `http://127.0.0.1:5000/json/?rec_id=36&refresh=true` . This
link will always get the latest results from the UNDL site for the given search.

# Format of XML
The search response is wrapped in a <records> tag.  Each search item returned from
the UNDL is in a <record> tag.  The user has a choice of what metadata they wish
to display.  Suppose they choose only title and related documents, then the XML will be
rather simple:
```xml
<records>
    <record>
    <related_documents>
        <related_document>S/2016/289</related_document>
        <related_document>S/PV.7659</related_document>
    </related_documents>
    <title>Resolution 2277 (2016) /</title>
    </record>
</records>
```

The following tags are used:
```xml<agenda>
<author>
<authority_authors>
<document_symbol>
<imprint>
<notes>
<note>
<publisher>
<pubyear>
<related_documents>
<related_document>
<subjects>
<subject>
<summary>
<title>
<voting_record>
```

# Limitations

Right now the Proxy App will fetch a maximum of 100 records.  This is to ensure a timely response.
If the user needs more than 100 records it is suggested they contact the DHL.

# History Feature

Clicking on the `History` button brings the user to a list of all searches.  From this view
there is a choice of `XML`, `JSON` and `Details`.

Clicking the `XML` or `JSON` buttons gives the XML or Json metadata for the search.  Clicking 
`Details` brings the user to a page with some of the info about the search as well as buttons
to refresh the Xml or JSON.

TBD: add pagination to the history page

# Setup

Install PostgreSQL
create database "proxy"
create role "proxy" with password "proxy"
grant all privileges in database "proxy" to role "proxy"
alter role proxy CREATEDB -- needed for testing

pip install -r requirements.txt

python create_db.py -- creates proxy database if it does not already exist

Copy config.py.default to config.py

For deployment purposes, change the host, database name, username, and password values to reflect your actual environment.
