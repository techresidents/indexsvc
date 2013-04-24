namespace java com.techresidents.services.indexsvc.gen
namespace py trindexsvc.gen

include "core.thrift"


/* Exceptions */

exception UnavailableException {
    1: string fault,
}
exception InvalidDataException {
    1: string fault,
}

/*
IndexData
   This is not the data that is actually being indexed, but
   it describes the data such that the index service can fetch
   the needed data from the db and index it.

   notBefore: the time to begin indexing (epoch timestamp)
   name: index name
   type: document type
   keys: list of db keys that need to be indexed
*/
struct IndexData {
    1: optional double notBefore,
    3: string name,
    4: string type,
    5: optional list<string> keys,
}

service TIndexService extends core.TRService
{
    /*
        Index data for the specified keys.
        Args:
            context: string representing the request context
            indexData: Thrift IndexData object. IndexData.keys required.
        Returns:
            None
    */
    void index(
        1: string context,
        2: IndexData indexData) throws (
                1:UnavailableException unavailableException,
                2:InvalidDataException invalidDataException),

    /*
        Index all data within the index.
        Args:
            context: string representing the request context
            indexData: Thrift IndexData object
        Returns:
            None
    */
    void indexAll(
        1: string context,
        2: IndexData indexData) throws (
                1:UnavailableException unavailableException,
                2:InvalidDataException invalidDataException),
}
