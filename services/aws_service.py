import boto3
from config.settings import settings
from models.schemas import ConversationLog
from typing import Dict, Any
from datetime import datetime
import json

class AWSService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket = settings.AWS_S3_BUCKET
        self.prefix = settings.AWS_S3_PREFIX
    
    async def store_conversation_log(
        self, 
        log: ConversationLog,
        additional_data: Dict[str, Any] = None
    ) -> bool:
        """Store conversation log in S3 for training and analysis"""
        try:
            # Prepare log data
            log_data = {
                "message_id": log.message_id,
                "user_phone": log.user_phone,
                "user_name": log.user_name,
                "message_type": log.message_type,
                "message_text": log.message_text,
                "intent": log.intent,
                "confidence": log.confidence,
                "response_sent": log.response_sent,
                "processing_time_ms": log.processing_time_ms,
                "estimated_cost": log.estimated_cost,
                "timestamp": log.timestamp.isoformat(),
                "jira_ticket_key": log.jira_ticket_key
            }
            
            # Add additional metadata
            if additional_data:
                log_data.update(additional_data)
            
            # Generate S3 key with date partitioning
            date_str = log.timestamp.strftime("%Y-%m-%d")
            timestamp_ms = int(log.timestamp.timestamp() * 1000)
            
            s3_key = f"{self.prefix}{date_str}/{timestamp_ms}-{log.user_phone}.json"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=json.dumps(log_data, indent=2),
                ContentType='application/json',
                Metadata={
                    'intent': log.intent or 'unknown',
                    'user_phone': log.user_phone,
                    'date': date_str
                }
            )
            
            print(f"📦 Log stored: {s3_key}")
            return True
            
        except Exception as e:
            print(f"Failed to store log in S3: {e}")
            return False
    
    async def get_cost_summary(self, date_str: str = None) -> Dict[str, Any]:
        """Calculate daily cost summary from logs"""
        try:
            if not date_str:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            # List all logs for the date
            prefix = f"{self.prefix}{date_str}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return {
                    "date": date_str,
                    "total_messages": 0,
                    "total_cost": 0.0
                }
            
            total_cost = 0.0
            message_count = 0
            
            for obj in response['Contents']:
                # Download and parse each log
                log_obj = self.s3_client.get_object(
                    Bucket=self.bucket,
                    Key=obj['Key']
                )
                
                log_data = json.loads(log_obj['Body'].read())
                total_cost += log_data.get('estimated_cost', 0.0)
                message_count += 1
            
            return {
                "date": date_str,
                "total_messages": message_count,
                "total_cost": round(total_cost, 4),
                "avg_cost_per_message": round(total_cost / message_count, 6) if message_count > 0 else 0
            }
            
        except Exception as e:
            print(f"Failed to calculate cost summary: {e}")
            return {
                "error": str(e)
            }

aws_service = AWSService()