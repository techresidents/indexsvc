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
   notBefore: the time to begin indexing (epoch timestamp)
   name: index name
   type: document type
   keys: list of db keys that need to be reindexed. Omit to reindex all keys.
*/
struct IndexData {
    1: optional double notBefore,
    2: string name,
    3: string type,
    4: optional list<i32> keys,
}

service TIndexService extends core.TRService
{
    /*
        Index data.
        Args:
            context: string representing the request context
            indexData: Thrift IndexData object
        Returns:
            None
    */
    void index(
        1: string context,
        2: IndexData indexData) throws (
                1:UnavailableException unavailableException,
                2:InvalidDataException invalidDataException),
}
