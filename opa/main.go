package main

import (
	"context"
	"fmt"
	"os"

	"github.com/open-policy-agent/opa/ast"
	"github.com/open-policy-agent/opa/cmd"
	"github.com/open-policy-agent/opa/rego"
	"github.com/open-policy-agent/opa/types"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// Global MongoDB client to be initialized during startup
var mongoClient *mongo.Client
var mongoDatabase string

func getFromEnv(var_name string) string {
	uri := os.Getenv(var_name)
	if uri == "" {
		msg := fmt.Sprintf("ENV VAR MISSING:: %s", var_name)
		panic(msg)
	}
	return uri
}

func initMongoClient(uri string, database string) error {
	clientOptions := options.Client().ApplyURI(uri)
	client, err := mongo.Connect(context.Background(), clientOptions)
	if err != nil {
		return err
	}

	// Verify connection
	err = client.Ping(context.Background(), nil)
	if err != nil {
		return err
	}

	mongoClient = client
	mongoDatabase = database
	return nil
}

func main() {
	// Initialize MongoDB connection (you'd typically get these from config)
	err := initMongoClient(getFromEnv("TAUTH_MONGODB_URI"), getFromEnv("TAUTH_MONGODB_DBNAME"))
	if err != nil {
		fmt.Println("Failed to connect to MongoDB:", err)
		os.Exit(1)
	}

	// Register MongoDB query as a built-in function
	rego.RegisterBuiltin2(
		&rego.Function{
			Name:             "mongodb.query",
			Decl:             types.NewFunction(types.Args(types.S, types.A), types.A),
			Memoize:          true,
			Nondeterministic: true,
		},
		func(bctx rego.BuiltinContext, a, b *ast.Term) (*ast.Term, error) {
			var collection string
			var queryMap map[string]interface{}

			// Extract collection name
			if err := ast.As(a.Value, &collection); err != nil {
				return nil, fmt.Errorf("first argument must be a string (collection name): %v", err)
			}

			// Extract query
			if err := ast.As(b.Value, &queryMap); err != nil {
				return nil, fmt.Errorf("second argument must be a map (query): %v", err)
			}

			// Perform MongoDB query
			results, err := performMongoQuery(collection, queryMap)
			if err != nil {
				return nil, err
			}

			// Convert results to AST value
			v, err := ast.InterfaceToValue(results)
			if err != nil {
				return nil, err
			}

			return ast.NewTerm(v), nil
		},
	)

	// Execute OPA
	if err := cmd.RootCommand.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

// performMongoQuery executes a query on the specified collection
func performMongoQuery(collection string, queryMap map[string]interface{}) ([]map[string]interface{}, error) {
	if mongoClient == nil {
		return nil, fmt.Errorf("MongoDB client not initialized")
	}

	// Get database and collection
	db := mongoClient.Database(mongoDatabase)
	coll := db.Collection(collection)

	// Convert query map to BSON
	query := bson.M(queryMap)

	// Execute query
	cursor, err := coll.Find(context.Background(), query)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(context.Background())

	// Decode results
	var results []map[string]interface{}
	if err = cursor.All(context.Background(), &results); err != nil {
		return nil, err
	}

	return results, nil
}
