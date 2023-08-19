# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from os import environ
import json
from datetime import datetime
from unittest import TestCase
from typing import Any, Dict
from uuid import uuid4
import yaml
import boto3
from boto3.dynamodb.conditions import Key
import moto


# Import the handler under test
from src import index as app

# Mock the DynamoDB Service during the test
@moto.mock_dynamodb

class TestSampleLambdaWithDynamoDB(TestCase):
    """
    Unit Test class for src/app.py
    """

    def setUp(self) -> None:
        """
        Test Set up:
           1. Create the lambda environment variale DYNAMODB_TABLE_NAME
           2. Build a DynamoDB Table according to the SAM template
           3. Create a random postfix for this test instance to prevent data collisions
           4. Populate DynamoDB Data into the Table for test
        """

        # Create a name for a test table, and set the environment
        self.test_ddb_table_name = "unit_test_ddb_table_name"
        environ["DYNAMODB_TABLE_NAME"] = self.test_ddb_table_name

        # Create a mock table using the definition from the SAM YAML template
        # This simple technique works if there are no intrinsics (like !If or !Ref) in the
        # resource properties for KeySchema, AttributeDefinitions.
        sam_template_table_properties = self.read_sam_template()["Resources"]["DynamoDBTable"]["Properties"]
        self.mock_dynamodb = boto3.resource("dynamodb")
        self.mock_dynamodb_table = self.mock_dynamodb.create_table(
                TableName = self.test_ddb_table_name,
                KeySchema = sam_template_table_properties["KeySchema"],
                AttributeDefinitions = sam_template_table_properties["AttributeDefinitions"],
                ProvisionedThroughput = sam_template_table_properties["ProvisionedThroughput"]
                )

        # Create a random postfix for the id's to prevent data collions between tests
        # Using unique id's per unit test will isolate test data
        self.id_postfix = "_" + str(uuid4())

        # Populate data for the tests
        self.mock_dynamodb_table.put_item(Item={'id': '1',
            'Weather': 'Sunny'})

    def tearDown(self) -> None:
        """
        For teardown, remove the mocked table & environment variable
        """
        self.mock_dynamodb_table.delete()
        del environ['DYNAMODB_TABLE_NAME']

    def read_sam_template(self, sam_template_fn : str = "template.yaml" ) -> dict:
        """
        Utility Function to read the SAM template for the current project
        """
        with open(sam_template_fn, "r") as fp:
            template =fp.read().replace("!","")   # Ignoring intrinsic tags
            return yaml.safe_load(template)

    def load_test_event(self, test_event_file_name: str) ->  Dict[str, Any]:
        """
        Load a sample event from a file
        Add the test isolation postfix to the path parameter {id}
        """
        with open(f"src/tests/events/{test_event_file_name}.json","r") as f:
            event = json.load(f)
            event["pathParameters"]["id"] = event["pathParameters"]["id"] + self.id_postfix
            return event


    def test_lambda_handler_post(self):
        """
        Test Post method on WeatherData
        """

        test_event = self.load_test_event("sampleEvent_POST_TEST001")
        test_return = app.lambda_handler(event=test_event,context=None)
        self.assertEqual( test_return["statusCode"] , 200)
        self.assertEqual( test_return["body"] , "Successfully inserted data!")

        # Verify the log entries

        id_items = self.mock_dynamodb_table.query(
            KeyConditionExpression=Key('id').eq('1')
        )

        # Log entry item to the original name item
        self.assertEqual( len(id_items["Items"]) , 1)


    def test_lambda_handler_delete(self):
        """
        Test delete method for WeatherData
        """

        test_event = self.load_test_event("sampleEvent_DELETE_TEST002")
        test_return = app.lambda_handler(event=test_event,context=None)
        self.assertEqual( test_return["statusCode"] , 200)
        self.assertEqual( test_return["body"] , "Successfully deleted data ID: 1!")

        # Verify the log entries

        id_items = self.mock_dynamodb_table.query(
            KeyConditionExpression=Key('id').eq('1')
        )

        # Log entry item to the original name item
        self.assertEqual(len(id_items["Items"]), 0)

    def test_invalid_arguments(self):
        """
        Test that both `id` and `Weather` should be preset in request body
        Otherwise raise error
        """
        test_event = self.load_test_event("sampleEvent_invalid_args_TEST003")
        test_return = app.lambda_handler(event=test_event,context=None)
        self.assertEqual( test_return["statusCode"] , 400)
        self.assertEqual( test_return["body"] , "'id' and/or 'Weather' not in request")

    def test_extra_arguments(self):
        """
        Test that only `id` and `Weather` should be present in request body
        Extra arguments should raise error
        """
        test_event = self.load_test_event("sampleEvent_extra_args_TEST004")
        test_return = app.lambda_handler(event=test_event,context=None)
        self.assertEqual( test_return["statusCode"] , 400)
        self.assertEqual( test_return["body"] , "Number of parameters are invalid")
