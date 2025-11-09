"""
Firestore service for storing and retrieving cover letters
"""
import os
from typing import Dict, Any, Optional
from datetime import datetime
from google.cloud import firestore
from google.oauth2 import service_account
from app.config import settings


class FirestoreService:
    def __init__(self):
        """Initialize Firestore client"""
        self.db = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Firestore client with service account"""
        try:
            service_account_path = settings.firebase_service_account_path
            if os.path.exists(service_account_path):
                credentials = service_account.Credentials.from_service_account_file(
                    service_account_path
                )
                self.db = firestore.Client(credentials=credentials)
                print("[Firestore] Initialized successfully")
            else:
                print(f"[Firestore] Warning: Service account file not found at {service_account_path}")
        except Exception as e:
            print(f"[Firestore] Error initializing: {e}")
            self.db = None
    
    def save_cover_letter(
        self,
        user_id: str,
        resume_text: str,
        job_title: str,
        company: str,
        job_description: str,
        cover_letter: str,
        bullets: list[str],
        pitch: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Save cover letter to Firestore
        
        Returns:
            Document ID if successful, None otherwise
        """
        if not self.db:
            print("[Firestore] Cannot save: Firestore not initialized")
            return None
        
        try:
            # Create document data
            doc_data = {
                "user_id": user_id,
                "resume_text": resume_text,
                "job_title": job_title,
                "company": company,
                "job_description": job_description,
                "cover_letter": cover_letter,
                "bullets": bullets,
                "pitch": pitch,
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
            
            # Add metadata if provided
            if metadata:
                doc_data["metadata"] = metadata
            
            # Save to Firestore collection: cover_letters
            doc_ref = self.db.collection("cover_letters").add(doc_data)
            doc_id = doc_ref[1].id
            
            print(f"[Firestore] Saved cover letter with ID: {doc_id}")
            return doc_id
            
        except Exception as e:
            print(f"[Firestore] Error saving cover letter: {e}")
            return None
    
    def get_cover_letter(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cover letter from Firestore
        
        Returns:
            Document data if found, None otherwise
        """
        if not self.db:
            print("[Firestore] Cannot retrieve: Firestore not initialized")
            return None
        
        try:
            doc_ref = self.db.collection("cover_letters").document(doc_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data["id"] = doc.id
                return data
            else:
                print(f"[Firestore] Document {doc_id} not found")
                return None
                
        except Exception as e:
            print(f"[Firestore] Error retrieving cover letter: {e}")
            return None
    
    def get_user_cover_letters(self, user_id: str, limit: int = 10) -> list[Dict[str, Any]]:
        """
        Get all cover letters for a user
        
        Returns:
            List of cover letter documents
        """
        if not self.db:
            print("[Firestore] Cannot retrieve: Firestore not initialized")
            return []
        
        try:
            query = (
                self.db.collection("cover_letters")
                .where("user_id", "==", user_id)
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            
            docs = query.stream()
            results = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            print(f"[Firestore] Error retrieving user cover letters: {e}")
            return []


# Singleton instance
firestore_service = FirestoreService()

