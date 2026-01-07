"""
Session Tracker - Lưu trữ và quản lý learning sessions

Lưu trữ:
- Session metadata (user_id, timestamps, name)
- Focus score history
- Event statistics
- Session summary

Hỗ trợ: 
- JSON file storage (có thể mở rộng sang DB)
- Export to CSV/JSON
- Query by user_id, date range
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import csv

from core.focus_scorer import FocusScorer


class SessionTracker:
    """
    Quản lý và lưu trữ focus tracking sessions
    """
    
    def __init__(self, storage_dir: str = "data/sessions"):
        """
        Args:
            storage_dir:  Thư mục lưu trữ session data
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata file
        self.metadata_file = self.storage_dir / "sessions_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load metadata từ file"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'sessions': {}}
    
    def _save_metadata(self):
        """Lưu metadata ra file"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def create_session_id(self, user_id: str) -> str:
        """
        Tạo session ID unique
        
        Format: {user_id}_{timestamp}
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{user_id}_{timestamp}"
    
    def save_session(
        self,
        session_id: str,
        user_id: str,
        scorer: FocusScorer,
        session_name: Optional[str] = None
    ):
        """
        Lưu session data
        
        Args:
            session_id: ID của session
            user_id: ID của user
            scorer: FocusScorer instance chứa data
            session_name: Tên session (optional)
        """
        # Get statistics
        stats = scorer.get_session_stats()
        
        # Prepare session data
        session_data = {
            'session_id':  session_id,
            'user_id': user_id,
            'session_name': session_name or f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            'started_at': datetime.fromtimestamp(scorer.history[0]['timestamp']).isoformat() if scorer.history else None,
            'ended_at': datetime.fromtimestamp(scorer.history[-1]['timestamp']).isoformat() if scorer.history else None,
            'statistics': stats,
            'focus_level_final': scorer.get_focus_level()[0],
        }
        
        # Save detailed history
        history_file = self.storage_dir / f"{session_id}_history.json"
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump({
                'session_info': session_data,
                'history': scorer.history
            }, f, indent=2, ensure_ascii=False)
        
        # Update metadata
        self.metadata['sessions'][session_id] = session_data
        self._save_metadata()
        
        print(f"✅ Session {session_id} saved successfully")
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Lấy thông tin session
        
        Returns:
            Session data hoặc None nếu không tìm thấy
        """
        return self.metadata['sessions'].get(session_id)
    
    def get_session_history(self, session_id: str) -> Optional[List[Dict]]:
        """
        Lấy chi tiết history của session
        """
        history_file = self.storage_dir / f"{session_id}_history.json"
        
        if not history_file.exists():
            return None
        
        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('history', [])
    
    def get_user_sessions(self, user_id: str, limit:  int = 50) -> List[Dict]:
        """
        Lấy tất cả sessions của một user
        
        Args: 
            user_id: ID của user
            limit: Số lượng sessions tối đa
        
        Returns:
            List of session data, sorted by date (newest first)
        """
        user_sessions = [
            session for session in self.metadata['sessions'].values()
            if session['user_id'] == user_id
        ]
        
        # Sort by ended_at (newest first)
        user_sessions.sort(
            key=lambda x: x.get('ended_at', ''),
            reverse=True
        )
        
        return user_sessions[:limit]
    
    def get_all_sessions(self, limit: int = 100) -> List[Dict]:
        """
        Lấy tất cả sessions
        """
        all_sessions = list(self.metadata['sessions'].values())
        
        # Sort by ended_at
        all_sessions.sort(
            key=lambda x: x.get('ended_at', ''),
            reverse=True
        )
        
        return all_sessions[:limit]
    
    def delete_session(self, session_id: str) -> bool:
        """
        Xóa session
        
        Returns:
            True nếu xóa thành công
        """
        if session_id not in self.metadata['sessions']: 
            return False
        
        # Delete history file
        history_file = self.storage_dir / f"{session_id}_history.json"
        if history_file.exists():
            history_file.unlink()
        
        # Remove from metadata
        del self.metadata['sessions'][session_id]
        self._save_metadata()
        
        print(f"🗑️ Session {session_id} deleted")
        return True
    
    def export_session_to_csv(self, session_id: str, output_path: Optional[str] = None) -> str:
        """
        Export session history sang CSV
        
        Returns:
            Path to exported CSV file
        """
        history = self.get_session_history(session_id)
        
        if not history:
            raise ValueError(f"Session {session_id} not found")
        
        # Default output path
        if output_path is None:
            output_path = self.storage_dir / f"{session_id}_export.csv"
        
        # Write CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if not history: 
                return str(output_path)
            
            # Get all event keys from first record
            event_keys = list(history[0].get('events', {}).keys())
            
            fieldnames = ['timestamp', 'datetime', 'score', 'score_raw', 'penalty', 'recovery'] + event_keys
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for record in history:
                row = {
                    'timestamp':  record['timestamp'],
                    'datetime':  datetime.fromtimestamp(record['timestamp']).isoformat(),
                    'score': round(record['score'], 2),
                    'score_raw': round(record['score_raw'], 2),
                    'penalty':  round(record['penalty'], 2),
                    'recovery': round(record['recovery'], 2),
                }
                
                # Add event columns
                for key in event_keys:
                    row[key] = record['events'].get(key, False)
                
                writer.writerow(row)
        
        print(f"📊 Session exported to:  {output_path}")
        return str(output_path)
    
    def get_user_statistics(self, user_id: str) -> Dict:
        """
        Tính toán thống kê tổng hợp cho user
        
        Returns:
            {
                'total_sessions': int,
                'total_duration': float (seconds),
                'avg_focus_score': float,
                'best_session': {...},
                'worst_session':  {...},
                'total_violations': int
            }
        """
        sessions = self.get_user_sessions(user_id, limit=1000)
        
        if not sessions:
            return {
                'total_sessions':  0,
                'message': 'No sessions found'
            }
        
        # Calculate statistics
        total_duration = sum(
            s['statistics'].get('duration_seconds', 0)
            for s in sessions
        )
        
        avg_scores = [s['statistics'].get('avg_score', 0) for s in sessions]
        avg_focus_score = sum(avg_scores) / len(avg_scores) if avg_scores else 0
        
        total_violations = sum(
            s['statistics'].get('total_violations', 0)
            for s in sessions
        )
        
        # Find best and worst sessions
        best_session = max(sessions, key=lambda x: x['statistics'].get('avg_score', 0))
        worst_session = min(sessions, key=lambda x: x['statistics'].get('avg_score', 0))
        
        return {
            'user_id': user_id,
            'total_sessions': len(sessions),
            'total_duration_seconds': round(total_duration, 2),
            'total_duration_hours': round(total_duration / 3600, 2),
            'avg_focus_score': round(avg_focus_score, 2),
            'total_violations': total_violations,
            'best_session': {
                'session_id': best_session['session_id'],
                'session_name': best_session['session_name'],
                'avg_score': round(best_session['statistics'].get('avg_score', 0), 2),
                'date': best_session.get('ended_at', '')
            },
            'worst_session': {
                'session_id': worst_session['session_id'],
                'session_name': worst_session['session_name'],
                'avg_score':  round(worst_session['statistics'].get('avg_score', 0), 2),
                'date': worst_session.get('ended_at', '')
            }
        }
    
    def cleanup_old_sessions(self, days:  int = 30) -> int:
        """
        Xóa sessions cũ hơn X ngày
        
        Args:
            days: Số ngày giữ lại
        
        Returns:
            Số sessions đã xóa
        """
        from datetime import timedelta
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        deleted_count = 0
        
        for session_id, session in list(self.metadata['sessions'].items()):
            ended_at = session.get('ended_at', '')
            
            if ended_at and ended_at < cutoff_date: 
                self.delete_session(session_id)
                deleted_count += 1
        
        print(f"🧹 Cleaned up {deleted_count} old sessions")
        return deleted_count


# ==================== CLI Interface (Optional) ====================

if __name__ == "__main__": 
    """
    CLI interface for session management
    
    Usage:
        python session_tracker.py list <user_id>
        python session_tracker.py stats <user_id>
        python session_tracker.py export <session_id>
        python session_tracker.py cleanup <days>
    """
    import sys
    
    tracker = SessionTracker()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python session_tracker.py list <user_id>")
        print("  python session_tracker.py stats <user_id>")
        print("  python session_tracker.py export <session_id>")
        print("  python session_tracker.py cleanup <days>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        if len(sys.argv) < 3:
            print("Error: user_id required")
            sys.exit(1)
        
        user_id = sys.argv[2]
        sessions = tracker.get_user_sessions(user_id)
        
        print(f"\n📋 Sessions for user:  {user_id}")
        print("=" * 80)
        
        for session in sessions:
            print(f"\nSession ID: {session['session_id']}")
            print(f"Name: {session['session_name']}")
            print(f"Date: {session.get('ended_at', 'N/A')}")
            print(f"Avg Score: {session['statistics'].get('avg_score', 0):.2f}")
            print(f"Duration: {session['statistics'].get('duration_seconds', 0):.0f}s")
    
    elif command == "stats": 
        if len(sys.argv) < 3:
            print("Error: user_id required")
            sys.exit(1)
        
        user_id = sys.argv[2]
        stats = tracker.get_user_statistics(user_id)
        
        print(f"\n📊 Statistics for user: {user_id}")
        print("=" * 80)
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    elif command == "export":
        if len(sys.argv) < 3:
            print("Error: session_id required")
            sys.exit(1)
        
        session_id = sys.argv[2]
        output_path = tracker.export_session_to_csv(session_id)
        print(f"✅ Exported to: {output_path}")
    
    elif command == "cleanup": 
        if len(sys.argv) < 3:
            print("Error: days required")
            sys.exit(1)
        
        days = int(sys.argv[2])
        deleted = tracker.cleanup_old_sessions(days)
        print(f"✅ Cleaned up {deleted} sessions older than {days} days")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)