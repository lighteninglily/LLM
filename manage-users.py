#!/usr/bin/env python3
"""
User Management for AnythingLLM

Create, manage, and invite users for your production deployment.

Usage:
    python3 manage-users.py create --email user@example.com --role admin
    python3 manage-users.py list
    python3 manage-users.py invite --email new-user@example.com
"""

import argparse
import requests
import sys
import json
from typing import Dict, Optional

class UserManager:
    """Manage AnythingLLM users"""
    
    def __init__(self, base_url: str = "http://localhost:3001", admin_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.headers = {"Accept": "application/json"}
        if admin_token:
            self.headers["Authorization"] = f"Bearer {admin_token}"
    
    def create_user(self, email: str, password: str, role: str = "default") -> Dict:
        """
        Create a new user
        
        Args:
            email: User email
            password: User password
            role: User role (admin, manager, default)
        """
        print(f"\nCreating user: {email}")
        print(f"Role: {role}")
        
        response = requests.post(
            f"{self.base_url}/api/admin/users/new",
            headers=self.headers,
            json={
                "username": email.split('@')[0],
                "password": password,
                "role": role
            }
        )
        
        if response.status_code in [200, 201]:
            user = response.json().get("user", {})
            print(f"✓ Created successfully")
            print(f"  Username: {user.get('username')}")
            print(f"  ID: {user.get('id')}")
            return user
        else:
            print(f"✗ Failed: {response.text}")
            return {}
    
    def list_users(self):
        """List all users"""
        response = requests.get(
            f"{self.base_url}/api/admin/users",
            headers=self.headers
        )
        
        if response.status_code == 200:
            users = response.json().get("users", [])
            print(f"\n{'='*60}")
            print(f"Users ({len(users)})")
            print(f"{'='*60}\n")
            
            for user in users:
                print(f"Username: {user.get('username')}")
                print(f"  ID: {user.get('id')}")
                print(f"  Role: {user.get('role')}")
                print(f"  Created: {user.get('createdAt')}")
                print()
        else:
            print(f"Failed to list users: {response.text}")
    
    def generate_invite_link(self, workspace_slug: str, role: str = "default") -> str:
        """
        Generate workspace invite link
        
        Args:
            workspace_slug: Workspace identifier
            role: Role for invited user
        """
        response = requests.post(
            f"{self.base_url}/api/workspace/{workspace_slug}/invite",
            headers=self.headers,
            json={"role": role}
        )
        
        if response.status_code in [200, 201]:
            invite = response.json()
            return invite.get("inviteUrl", "")
        return ""


def main():
    parser = argparse.ArgumentParser(description="Manage AnythingLLM users")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Create user
    create_parser = subparsers.add_parser("create", help="Create new user")
    create_parser.add_argument("--email", required=True, help="User email")
    create_parser.add_argument("--password", required=True, help="User password")
    create_parser.add_argument("--role", default="default", 
                              choices=["admin", "manager", "default"],
                              help="User role")
    
    # List users
    subparsers.add_parser("list", help="List all users")
    
    # Invite
    invite_parser = subparsers.add_parser("invite", help="Generate invite link")
    invite_parser.add_argument("--workspace", required=True, help="Workspace slug")
    invite_parser.add_argument("--role", default="default", help="User role")
    
    # Global options
    parser.add_argument("--url", default="http://localhost:3001", 
                       help="AnythingLLM server URL")
    parser.add_argument("--token", help="Admin API token")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = UserManager(args.url, args.token)
    
    if args.command == "create":
        manager.create_user(args.email, args.password, args.role)
    elif args.command == "list":
        manager.list_users()
    elif args.command == "invite":
        link = manager.generate_invite_link(args.workspace, args.role)
        print(f"\nInvite link:\n{link}\n")


if __name__ == "__main__":
    main()
