import os
import logging
from typing import Dict, List, Any, Union, Optional
from datetime import datetime
from bson import ObjectId
from pymongo.mongo_client import MongoClient as PyMongoClient
from pymongo.server_api import ServerApi
from pymongo.collection import Collection
from pymongo.errors import PyMongoError, DuplicateKeyError, BulkWriteError
from pymongo.results import InsertOneResult, InsertManyResult, UpdateResult, DeleteResult
from pymongo import IndexModel, ASCENDING, DESCENDING
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mongo_client')

uri = f"mongodb+srv://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@cluster0.xljk6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

class MongoDBClient:
    """
    A comprehensive MongoDB client for AI agent interactions.
    Provides methods for all common database operations with error handling.
    """
    
    def __init__(self, database_name: str, connection_string:str, connect_timeout: int = 5000):
        """
        Initialize the MongoDB client with the specified database.
        
        Args:
            database_name: The name of the database to connect to
            connect_timeout: Connection timeout in milliseconds
        """
        try:
            # Create a new client and connect to the server with appropriate options
            self.client = PyMongoClient(
                connection_string,
                server_api=ServerApi('1'),
                connectTimeoutMS=connect_timeout,
                retryWrites=True,
                w='majority'
            )

            # Send a ping to confirm a successful connection
            self.client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB cluster for database '{database_name}'")
            
            # Get the database
            self.db = self.client[database_name]
            
            # Initialize transaction session
            self.session = None
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    # Collection Management Methods
    def list_collections(self) -> List[str]:
        """
        List all collections in the database.
        
        Returns:
            List of collection names
        """
        try:
            return self.db.list_collection_names()
        except PyMongoError as e:
            logger.error(f"Failed to list collections: {str(e)}")
            raise

    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a collection object for the specified collection name.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            PyMongo Collection object
        """
        return self.db[collection_name]
    
    def create_collection(self, collection_name: str, options: Dict = None) -> bool:
        """
        Create a new collection with optional validation schema.
        
        Args:
            collection_name: Name of the collection to create
            options: Optional configuration for the collection (validation, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if options:
                self.db.create_collection(collection_name, **options)
            else:
                self.db.create_collection(collection_name)
            logger.info(f"Created collection '{collection_name}'")
            return True
        except PyMongoError as e:
            logger.error(f"Failed to create collection '{collection_name}': {str(e)}")
            return False
    
    def drop_collection(self, collection_name: str) -> bool:
        """
        Drop a collection from the database.
        
        Args:
            collection_name: Name of the collection to drop
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.db.drop_collection(collection_name)
            logger.info(f"Dropped collection '{collection_name}'")
            return True
        except PyMongoError as e:
            logger.error(f"Failed to drop collection '{collection_name}': {str(e)}")
            return False

    # Document Operations - Create
    def insert_one(self, collection_name: str, document: Dict) -> Optional[str]:
        """
        Insert a single document into the specified collection.
        
        Args:
            collection_name: Name of the collection
            document: Document to insert
            
        Returns:
            ID of inserted document or None if failed
        """
        try:
            # Add creation timestamp if not present
            if 'createdAt' not in document:
                document['createdAt'] = datetime.utcnow()
                
            result: InsertOneResult = self.db[collection_name].insert_one(document)
            logger.info(f"Inserted document with ID {result.inserted_id} into '{collection_name}'")
            return str(result.inserted_id)
        except DuplicateKeyError:
            logger.error(f"Failed to insert document - duplicate key error")
            return None
        except PyMongoError as e:
            logger.error(f"Failed to insert document: {str(e)}")
            return None
    
    def insert_many(self, collection_name: str, documents: List[Dict], ordered: bool = True) -> List[str]:
        """
        Insert multiple documents into the specified collection.
        
        Args:
            collection_name: Name of the collection
            documents: List of documents to insert
            ordered: Whether insertion should be ordered (stop on first error)
            
        Returns:
            List of inserted document IDs
        """
        try:
            # Add creation timestamp if not present in documents
            for doc in documents:
                if 'createdAt' not in doc:
                    doc['createdAt'] = datetime.utcnow()
                    
            result: InsertManyResult = self.db[collection_name].insert_many(documents, ordered=ordered)
            inserted_ids = [str(id) for id in result.inserted_ids]
            logger.info(f"Inserted {len(inserted_ids)} documents into '{collection_name}'")
            return inserted_ids
        except BulkWriteError as e:
            successful_ids = [str(doc_id) for doc_id in e.details.get('inserted_ids', [])]
            logger.error(f"Partial bulk write failure: {len(successful_ids)} documents inserted, {len(documents) - len(successful_ids)} failed")
            return successful_ids
        except PyMongoError as e:
            logger.error(f"Failed to bulk insert documents: {str(e)}")
            return []

    # Document Operations - Read
    def find_one(self, collection_name: str, query: Dict, projection: Dict = None) -> Optional[Dict]:
        """
        Find a single document that matches the query.
        
        Args:
            collection_name: Name of the collection
            query: Query filter to apply
            projection: Optional fields to include/exclude
            
        Returns:
            Matching document or None if not found
        """
        try:
            result = self.db[collection_name].find_one(query, projection)
            if result and '_id' in result and isinstance(result['_id'], ObjectId):
                result['_id'] = str(result['_id'])
            return result
        except PyMongoError as e:
            logger.error(f"Failed to find document: {str(e)}")
            return None

    def find_by_id(self, collection_name: str, document_id: str, projection: Dict = None) -> Optional[Dict]:
        """
        Find a document by its ID.
        
        Args:
            collection_name: Name of the collection
            document_id: ID of the document to find
            projection: Optional fields to include/exclude
            
        Returns:
            Matching document or None if not found
        """
        try:
            object_id = ObjectId(document_id)
            result = self.db[collection_name].find_one({'_id': object_id}, projection)
            if result:
                result['_id'] = str(result['_id'])
            return result
        except PyMongoError as e:
            logger.error(f"Failed to find document by ID '{document_id}': {str(e)}")
            return None
    
    def find_many(self, 
                  collection_name: str, 
                  query: Dict = None, 
                  projection: Dict = None, 
                  sort: List = None, 
                  limit: int = 0, 
                  skip: int = 0) -> List[Dict]:
        """
        Find documents that match the query with pagination.
        
        Args:
            collection_name: Name of the collection
            query: Query filter to apply (None for all documents)
            projection: Optional fields to include/exclude
            sort: Optional sorting parameters [(field, direction), ...]
            limit: Maximum number of results (0 for all)
            skip: Number of documents to skip
            
        Returns:
            List of matching documents
        """
        if query is None:
            query = {}
            
        try:
            cursor = self.db[collection_name].find(query, projection)
            
            if sort:
                cursor = cursor.sort(sort)
            
            if skip > 0:
                cursor = cursor.skip(skip)
                
            if limit > 0:
                cursor = cursor.limit(limit)
            
            # Convert ObjectId to string
            result = []
            for doc in cursor:
                if '_id' in doc and isinstance(doc['_id'], ObjectId):
                    doc['_id'] = str(doc['_id'])
                result.append(doc)
                
            return result
        except PyMongoError as e:
            logger.error(f"Failed to find documents: {str(e)}")
            return []

    def count_documents(self, collection_name: str, query: Dict = None) -> int:
        """
        Count documents that match the query.
        
        Args:
            collection_name: Name of the collection
            query: Query filter to apply (None for all documents)
            
        Returns:
            Count of matching documents
        """
        if query is None:
            query = {}
            
        try:
            return self.db[collection_name].count_documents(query)
        except PyMongoError as e:
            logger.error(f"Failed to count documents: {str(e)}")
            return 0

    # Document Operations - Update
    def update_one(self, 
                   collection_name: str, 
                   query: Dict, 
                   update: Dict, 
                   upsert: bool = False) -> Optional[UpdateResult]:
        """
        Update a single document that matches the query.
        
        Args:
            collection_name: Name of the collection
            query: Query filter to apply
            update: Update operations to perform
            upsert: Whether to insert if no matching document exists
            
        Returns:
            UpdateResult object or None if failed
        """
        try:
            # Add last modified timestamp if using $set operator
            if '$set' in update:
                update['$set']['updatedAt'] = datetime.utcnow()
            else:
                update['$set'] = {'updatedAt': datetime.utcnow()}
                
            result = self.db[collection_name].update_one(query, update, upsert=upsert)
            logger.info(f"Updated {result.modified_count} document(s) in '{collection_name}'")
            return result
        except PyMongoError as e:
            logger.error(f"Failed to update document: {str(e)}")
            return None

    def update_by_id(self, 
                     collection_name: str, 
                     document_id: str, 
                     update: Dict, 
                     upsert: bool = False) -> Optional[UpdateResult]:
        """
        Update a document by its ID.
        
        Args:
            collection_name: Name of the collection
            document_id: ID of the document to update
            update: Update operations to perform
            upsert: Whether to insert if no matching document exists
            
        Returns:
            UpdateResult object or None if failed
        """
        try:
            object_id = ObjectId(document_id)
            
            # Add last modified timestamp if using $set operator
            if '$set' in update:
                update['$set']['updatedAt'] = datetime.utcnow()
            else:
                update['$set'] = {'updatedAt': datetime.utcnow()}
                
            result = self.db[collection_name].update_one({'_id': object_id}, update, upsert=upsert)
            logger.info(f"Updated document with ID '{document_id}' in '{collection_name}'")
            return result
        except PyMongoError as e:
            logger.error(f"Failed to update document by ID '{document_id}': {str(e)}")
            return None
    
    def update_many(self, 
                    collection_name: str, 
                    query: Dict, 
                    update: Dict, 
                    upsert: bool = False) -> Optional[UpdateResult]:
        """
        Update multiple documents that match the query.
        
        Args:
            collection_name: Name of the collection
            query: Query filter to apply
            update: Update operations to perform
            upsert: Whether to insert if no matching document exists
            
        Returns:
            UpdateResult object or None if failed
        """
        try:
            # Add last modified timestamp if using $set operator
            if '$set' in update:
                update['$set']['updatedAt'] = datetime.utcnow()
            else:
                update['$set'] = {'updatedAt': datetime.utcnow()}
                
            result = self.db[collection_name].update_many(query, update, upsert=upsert)
            logger.info(f"Updated {result.modified_count} document(s) in '{collection_name}'")
            return result
        except PyMongoError as e:
            logger.error(f"Failed to update documents: {str(e)}")
            return None
    
    def replace_one(self, 
                    collection_name: str, 
                    query: Dict, 
                    replacement: Dict, 
                    upsert: bool = False) -> Optional[UpdateResult]:
        """
        Replace a single document that matches the query.
        
        Args:
            collection_name: Name of the collection
            query: Query filter to apply
            replacement: Complete replacement document
            upsert: Whether to insert if no matching document exists
            
        Returns:
            UpdateResult object or None if failed
        """
        try:
            # Add timestamps
            replacement['updatedAt'] = datetime.utcnow()
            if 'createdAt' not in replacement:
                replacement['createdAt'] = datetime.utcnow()
                
            result = self.db[collection_name].replace_one(query, replacement, upsert=upsert)
            logger.info(f"Replaced {result.modified_count} document(s) in '{collection_name}'")
            return result
        except PyMongoError as e:
            logger.error(f"Failed to replace document: {str(e)}")
            return None

    # Document Operations - Delete
    def delete_one(self, collection_name: str, query: Dict) -> Optional[DeleteResult]:
        """
        Delete a single document that matches the query.
        
        Args:
            collection_name: Name of the collection
            query: Query filter to apply
            
        Returns:
            DeleteResult object or None if failed
        """
        try:
            result = self.db[collection_name].delete_one(query)
            logger.info(f"Deleted {result.deleted_count} document(s) from '{collection_name}'")
            return result
        except PyMongoError as e:
            logger.error(f"Failed to delete document: {str(e)}")
            return None

    def delete_by_id(self, collection_name: str, document_id: str) -> Optional[DeleteResult]:
        """
        Delete a document by its ID.
        
        Args:
            collection_name: Name of the collection
            document_id: ID of the document to delete
            
        Returns:
            DeleteResult object or None if failed
        """
        try:
            object_id = ObjectId(document_id)
            result = self.db[collection_name].delete_one({'_id': object_id})
            logger.info(f"Deleted document with ID '{document_id}' from '{collection_name}'")
            return result
        except PyMongoError as e:
            logger.error(f"Failed to delete document by ID '{document_id}': {str(e)}")
            return None
    
    def delete_many(self, collection_name: str, query: Dict) -> Optional[DeleteResult]:
        """
        Delete multiple documents that match the query.
        
        Args:
            collection_name: Name of the collection
            query: Query filter to apply
            
        Returns:
            DeleteResult object or None if failed
        """
        try:
            result = self.db[collection_name].delete_many(query)
            logger.info(f"Deleted {result.deleted_count} document(s) from '{collection_name}'")
            return result
        except PyMongoError as e:
            logger.error(f"Failed to delete documents: {str(e)}")
            return None

    # Advanced Query Operations
    def aggregate(self, collection_name: str, pipeline: List[Dict]) -> List[Dict]:
        """
        Perform an aggregation pipeline query.
        
        Args:
            collection_name: Name of the collection
            pipeline: MongoDB aggregation pipeline
            
        Returns:
            List of results from the aggregation
        """
        try:
            result = list(self.db[collection_name].aggregate(pipeline))
            
            # Convert ObjectId to string in results
            for doc in result:
                if '_id' in doc and isinstance(doc['_id'], ObjectId):
                    doc['_id'] = str(doc['_id'])
            
            return result
        except PyMongoError as e:
            logger.error(f"Failed to execute aggregation: {str(e)}")
            return []

    def distinct(self, collection_name: str, field: str, query: Dict = None) -> List:
        """
        Get distinct values for a field across a collection.
        
        Args:
            collection_name: Name of the collection
            field: Field to find distinct values for
            query: Optional query to filter documents
            
        Returns:
            List of distinct values
        """
        try:
            return self.db[collection_name].distinct(field, filter=query)
        except PyMongoError as e:
            logger.error(f"Failed to get distinct values: {str(e)}")
            return []

    # Index Management
    def create_index(self, 
                     collection_name: str, 
                     keys: Union[str, List, Dict],
                     unique: bool = False, 
                     background: bool = True,
                     name: str = None) -> str:
        """
        Create an index on the collection.
        
        Args:
            collection_name: Name of the collection
            keys: Index specification (field name or list of tuples)
            unique: Whether the index should enforce uniqueness
            background: Whether the index should be built in the background
            name: Optional custom name for the index
            
        Returns:
            Name of the created index
        """
        try:
            options = {
                'unique': unique,
                'background': background
            }
            
            if name:
                options['name'] = name
                
            result = self.db[collection_name].create_index(keys, **options)
            logger.info(f"Created index '{result}' on collection '{collection_name}'")
            return result
        except PyMongoError as e:
            logger.error(f"Failed to create index: {str(e)}")
            return ""

    def create_indexes(self, collection_name: str, indexes: List[Dict]) -> List[str]:
        """
        Create multiple indexes on the collection.
        
        Args:
            collection_name: Name of the collection
            indexes: List of index specifications
            
        Returns:
            List of created index names
        """
        try:
            index_models = []
            for idx in indexes:
                keys = idx.get('keys')
                options = {k: v for k, v in idx.items() if k != 'keys'}
                index_models.append(IndexModel(keys, **options))
                
            result = self.db[collection_name].create_indexes(index_models)
            logger.info(f"Created {len(result)} indexes on collection '{collection_name}'")
            return result
        except PyMongoError as e:
            logger.error(f"Failed to create indexes: {str(e)}")
            return []

    def list_indexes(self, collection_name: str) -> List[Dict]:
        """
        List all indexes on the collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            List of index information
        """
        try:
            return list(self.db[collection_name].list_indexes())
        except PyMongoError as e:
            logger.error(f"Failed to list indexes: {str(e)}")
            return []

    def drop_index(self, collection_name: str, index_name: str) -> bool:
        """
        Drop an index from the collection.
        
        Args:
            collection_name: Name of the collection
            index_name: Name of the index to drop
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.db[collection_name].drop_index(index_name)
            logger.info(f"Dropped index '{index_name}' from collection '{collection_name}'")
            return True
        except PyMongoError as e:
            logger.error(f"Failed to drop index: {str(e)}")
            return False

    def drop_all_indexes(self, collection_name: str) -> bool:
        """
        Drop all indexes from the collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.db[collection_name].drop_indexes()
            logger.info(f"Dropped all indexes from collection '{collection_name}'")
            return True
        except PyMongoError as e:
            logger.error(f"Failed to drop indexes: {str(e)}")
            return False

    # Transaction Support
    def start_transaction(self):
        """
        Start a new transaction session.
        """
        try:
            if self.session:
                self.session.end_session()
                
            self.session = self.client.start_session()
            self.session.start_transaction()
            logger.info("Started new transaction")
        except PyMongoError as e:
            logger.error(f"Failed to start transaction: {str(e)}")
            raise

    def commit_transaction(self):
        """
        Commit the current transaction.
        """
        try:
            if self.session and self.session.in_transaction:
                self.session.commit_transaction()
                logger.info("Committed transaction")
        except PyMongoError as e:
            logger.error(f"Failed to commit transaction: {str(e)}")
            raise
        finally:
            if self.session:
                self.session.end_session()
                self.session = None

    def abort_transaction(self):
        """
        Abort the current transaction.
        """
        try:
            if self.session and self.session.in_transaction:
                self.session.abort_transaction()
                logger.info("Aborted transaction")
        except PyMongoError as e:
            logger.error(f"Failed to abort transaction: {str(e)}")
            raise
        finally:
            if self.session:
                self.session.end_session()
                self.session = None

    # Bulk Operations
    def bulk_write(self, collection_name: str, operations: List, ordered: bool = True) -> Dict:
        """
        Execute a bulk write operation.
        
        Args:
            collection_name: Name of the collection
            operations: List of write operations
            ordered: Whether execution should be ordered
            
        Returns:
            Dictionary with bulk write results
        """
        try:
            result = self.db[collection_name].bulk_write(operations, ordered=ordered)
            logger.info(f"Bulk write operation completed: {result.inserted_count} inserted, "
                        f"{result.modified_count} modified, {result.deleted_count} deleted")
            
            return {
                'inserted_count': result.inserted_count,
                'matched_count': result.matched_count,
                'modified_count': result.modified_count,
                'deleted_count': result.deleted_count,
                'upserted_count': result.upserted_count,
                'upserted_ids': [str(id) for id in result.upserted_ids.values()]
            }
        except BulkWriteError as e:
            logger.error(f"Bulk write error: {str(e)}")
            return {
                'error': True,
                'message': str(e),
                'details': e.details
            }
        except PyMongoError as e:
            logger.error(f"Failed to execute bulk write: {str(e)}")
            return {'error': True, 'message': str(e)}

    # Database Management
    def get_database_stats(self) -> Dict:
        """
        Get statistics about the current database.
        
        Returns:
            Dictionary with database statistics
        """
        try:
            return self.db.command('dbStats')
        except PyMongoError as e:
            logger.error(f"Failed to get database stats: {str(e)}")
            return {}

    def get_collection_stats(self, collection_name: str) -> Dict:
        """
        Get statistics about a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dictionary with collection statistics
        """
        try:
            return self.db.command('collStats', collection_name)
        except PyMongoError as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {}

    def create_backup(self, output_dir: str) -> bool:
        """
        Create a backup of the database using mongodump.
        Note: This requires mongodump to be installed and in PATH.
        
        Args:
            output_dir: Directory to store backup
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import subprocess
            db_name = self.db.name
            connection_string = uri
            
            cmd = [
                'mongodump',
                '--uri', connection_string,
                '--db', db_name,
                '--out', output_dir
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Backup failed: {stderr.decode()}")
                return False
                
            logger.info(f"Successfully backed up database '{db_name}' to {output_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            return False

    # Health and Monitoring
    def ping(self) -> bool:
        """
        Check if the MongoDB server is responsive.
        
        Returns:
            True if responsive, False otherwise
        """
        try:
            self.client.admin.command('ping')
            return True
        except PyMongoError:
            return False

    def get_server_status(self) -> Dict:
        """
        Get the status of the MongoDB server.
        
        Returns:
            Dictionary with server status information
        """
        try:
            return self.client.admin.command('serverStatus')
        except PyMongoError as e:
            logger.error(f"Failed to get server status: {str(e)}")
            return {}

    # Cleanup
    def close(self):
        """
        Close the MongoDB connection.
        """
        if self.session:
            try:
                if self.session.in_transaction:
                    self.session.abort_transaction()
                self.session.end_session()
            except Exception as e:
                logger.error(f"Error ending session: {str(e)}")
            
        if self.client:
            try:
                self.client.close()
                logger.info("MongoDB connection closed")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {str(e)}")