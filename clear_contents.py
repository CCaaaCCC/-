"""
清空教学内容数据脚本

使用方法：
    .venv/Scripts/python.exe clear_contents.py

注意：此脚本会删除所有教学内容和分类！
"""

from app.db.session import engine, SessionLocal
from app.db.models import ContentCategory, TeachingContent, StudentLearningRecord, ContentComment

def clear_contents():
    db = SessionLocal()
    
    try:
        # 删除所有内容相关数据
        content_count = db.query(TeachingContent).count()
        comment_count = db.query(ContentComment).count()
        record_count = db.query(StudentLearningRecord).count()
        category_count = db.query(ContentCategory).count()
        
        print(f"当前数据：")
        print(f"  - 教学内容：{content_count} 条")
        print(f"  - 评论：{comment_count} 条")
        print(f"  - 学习记录：{record_count} 条")
        print(f"  - 分类：{category_count} 个")
        
        confirm = input("\n⚠️  确定要删除所有数据吗？(yes/no): ")
        if confirm.lower() != 'yes':
            print("已取消")
            return
        
        # 删除数据（注意顺序：先删除外键关联的表）
        db.query(ContentComment).delete()
        db.query(StudentLearningRecord).delete()
        db.query(TeachingContent).delete()

        # ContentCategory 使用自引用外键 parent_id，不能一次性删除所有行。
        # 按叶子结点（没有子分类的条目）循环删除，直到没有剩余分类。
        while True:
            leaves = db.query(ContentCategory).filter(~ContentCategory.children.any()).all()
            if not leaves:
                break
            for leaf in leaves:
                db.delete(leaf)
            db.commit()

        # 如果仍有残留（理论上不会，但为保险起见），先将 parent_id 置空再删除。
        remaining = db.query(ContentCategory).count()
        if remaining:
            db.query(ContentCategory).update({ContentCategory.parent_id: None})
            db.commit()
            db.query(ContentCategory).delete()
            db.commit()
        
        print("\n✅ 已清空所有教学内容数据")
        print("   现在可以运行 init_sample_contents.py 重新初始化示例内容")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 清空失败：{e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🗑️  清空教学内容数据")
    clear_contents()
