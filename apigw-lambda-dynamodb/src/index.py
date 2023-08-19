# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import sys
import os
import json
import boto3
dynamodb_client = boto3.client('dynamodb')


def lambda_handler(event, context):
    """
    POST and DELETE methods take request body as below
        {
        "id": "<number>",
        "Weather": "<weather>"
        }
    """
    try:
        request_body = json.loads(event.get('body'))
        # Check that json request should only contain `id` and `Weather`
        if 'id' not in request_body.keys() or 'Weather' not in request_body.keys():
            return {
            'statusCode': 400,
            'body': "'id' and/or 'Weather' not in request"
            }
            # Request should not contain keys other than `id` and `Weather`
        elif len(request_body.keys()) > 2:
            return {
            'statusCode': 400,
            'body': "Number of parameters are invalid"
            }
        item = {'id': {'S': request_body['id']},
            'Weather': {'S': request_body['Weather']}}

        if event['httpMethod'] == 'POST':

            dynamodb_client.put_item(TableName=os.environ['DYNAMODB_TABLE_NAME'], Item=item)
            return {
                'statusCode': 200,
                'body': 'Successfully inserted data!'
                }

        elif event['httpMethod'] == 'DELETE':
            # item = dynamodb_client.get_item(TableName=os.environ['DYNAMODB_TABLE_NAME'],
            #     Key=item)
            dynamodb_client.delete_item(TableName=os.environ['DYNAMODB_TABLE_NAME'], Key=item)
            return {
                'statusCode': 200,
                'body': 'Successfully deleted data ID: {}!'.format(item['id']['S'])
                }
    except Exception as e:
        return {
            'statusCode': 200,
            'body': str(e)
            }
