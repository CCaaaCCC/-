"""
初始化示例教学内容脚本

使用方法：
    .venv/Scripts/python.exe init_sample_contents.py

此脚本用于在数据库中创建示例教学内容，供教学演示使用。
"""

from app.db.session import engine, SessionLocal
from app.db.models import TeachingContent, User

def init_sample_contents():
    db = SessionLocal()
    
    try:
        # 获取管理员用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        admin_id = admin_user.id if admin_user else 1
        
        # 检查是否已有内容
        existing_count = db.query(TeachingContent).count()
        if existing_count > 0:
            print(f"⚠️  数据库中已有 {existing_count} 条内容，跳过初始化")
            print("   如需重新初始化，请先清空 teaching_contents 表")
            return
        
        # 添加示例教学内容
        sample_contents = [
            TeachingContent(
                title="番茄的生长周期",
                tags="农作物,番茄,生长周期",
                content_type="article",
                content="""# 番茄的生长周期

番茄是一种喜温作物，生长适温为 **20-25℃**。从播种到收获一般需要 **90-120 天**。

## 生长阶段

### 1. 发芽期（7-10 天）
- 适宜温度：25-28℃
- 土壤湿度：60-70%
- 注意事项：保持土壤湿润，避免积水

### 2. 幼苗期（25-30 天）
- 适宜温度：20-25℃（白天），15-18℃（夜间）
- 光照：每天 8-10 小时
- 注意事项：防止徒长，适时通风

### 3. 开花期（15-20 天）
- 适宜温度：25-28℃
- 湿度：50-60%
- 注意事项：人工授粉可提高坐果率

### 4. 结果期（40-50 天）
- 适宜温度：25-30℃
- 水分：均匀供应，避免忽干忽湿
- 注意事项：及时摘除畸形果

## 环境要求

| 因素 | 要求 |
|------|------|
| 温度 | 20-30℃ |
| 光照 | 充足，每天 6-8 小时 |
| 水分 | 土壤湿度 60-80% |
| 土壤 | 疏松肥沃，pH 6.0-7.0 |

## 常见问题

1. **落花落果**：温度过高或过低、水分不均
2. **裂果**：水分供应不均匀
3. **脐腐病**：缺钙引起

> 提示：定期检查植株状态，及时调整环境参数。
""",
                is_published=True,
                author_id=admin_id,
                cover_image="https://picsum.photos/seed/tomato/400/200"
            ),
            TeachingContent(
                title="黄瓜种植指南",
                tags="农作物,黄瓜,种植",
                content_type="article",
                content="""# 黄瓜种植指南

黄瓜是喜温、喜湿、喜光的作物，适合在温暖湿润的环境中生长。

## 生长条件

- **温度**：生长适温 18-32℃，夜间 15-18℃
- **湿度**：空气湿度 70-90%，土壤湿度 80-90%
- **光照**：每天 6-8 小时直射阳光

## 种植步骤

1. 选择优质种子
2. 浸种催芽（25-30℃温水浸泡 4-6 小时）
3. 播种育苗
4. 移栽定植
5. 田间管理
6. 适时采收

## 水肥管理

### 浇水原则
- 苗期：少浇勤浇
- 开花期：控制浇水
- 结果期：充足供水

### 施肥要点
- 基肥：有机肥为主
- 追肥：氮磷钾配合
""",
                is_published=True,
                author_id=admin_id
            ),
            TeachingContent(
                title="光合作用的原理",
                tags="自然科学,光合作用,基础理论",
                content_type="article",
                content="""# 光合作用的原理

光合作用是植物、藻类和某些细菌利用光能将二氧化碳和水转化为有机物的过程。

## 基本公式

```
6CO₂ + 6H₂O + 光能 → C₆H₁₂O₆ + 6O₂
```

## 光合作用的两个阶段

### 1. 光反应
- 发生场所：叶绿体类囊体膜
- 需要条件：光照、水、光合色素
- 产物：ATP、NADPH、O₂

### 2. 暗反应（卡尔文循环）
- 发生场所：叶绿体基质
- 需要条件：CO₂、ATP、NADPH
- 产物：葡萄糖

## 影响光合作用的因素

| 因素 | 影响 |
|------|------|
| 光照强度 | 光照越强，光合作用越旺盛（但有饱和点） |
| 二氧化碳浓度 | CO₂浓度增加可提高光合速率 |
| 温度 | 影响酶的活性，最适温度约 25℃ |
| 水分 | 缺水会导致气孔关闭，影响 CO₂吸收 |

## 实际应用

1. **合理密植**：充分利用光能
2. **间作套种**：提高光能利用率
3. **温室栽培**：控制环境条件
""",
                is_published=True,
                author_id=admin_id
            ),
            TeachingContent(
                title="植物细胞结构",
                tags="植物百科,细胞结构,生物学",
                content_type="article",
                content="""# 植物细胞结构

植物细胞是真核细胞，具有细胞壁、叶绿体等特有结构。

## 主要结构

### 细胞壁
- 成分：纤维素、半纤维素、果胶
- 功能：支持和保护细胞

### 细胞膜
- 结构：磷脂双分子层
- 功能：控制物质进出

### 细胞核
- 组成：核膜、核仁、染色质
- 功能：遗传信息库

### 叶绿体
- 结构：双层膜，内含类囊体
- 功能：光合作用场所

### 液泡
- 特点：成熟植物细胞有一个中央大液泡
- 功能：储存物质、维持细胞形态

### 线粒体
- 功能：细胞呼吸场所，产生 ATP
""",
                is_published=True,
                author_id=admin_id
            ),
            TeachingContent(
                title="大棚温度对比实验",
                tags="实验指导,温度实验,课堂实践",
                content_type="article",
                content="""# 大棚温度对比实验

## 实验目的
探究不同温度对植物生长的影响

## 实验材料
- 相同品种的植物幼苗 6 株
- 3 个可独立控温的大棚
- 温度计、湿度计
- 测量工具

## 实验步骤

### 第一步：分组设置
| 组别 | 温度设置 | 植株数 |
|------|----------|--------|
| A 组 | 15℃（低温） | 2 株 |
| B 组 | 25℃（适温） | 2 株 |
| C 组 | 35℃（高温） | 2 株 |

### 第二步：日常管理
1. 每天定时浇水（等量）
2. 保持光照时间一致
3. 记录环境参数

### 第三步：数据记录
连续观察 14 天，每天记录：
- 株高
- 叶片数
- 叶片颜色
- 生长状态

## 预期结果

- **B 组（25℃）**：生长最好，株高增长快，叶片翠绿
- **A 组（15℃）**：生长缓慢，叶片可能发黄
- **C 组（35℃）**：可能出现萎蔫，生长受阻

## 实验结论

植物生长有最适温度范围，过高或过低的温度都会影响正常生长。
""",
                is_published=True,
                author_id=admin_id
            ),
        ]
        
        for content in sample_contents:
            db.add(content)
        
        db.commit()
        
        print(f"✅ 成功添加 {len(sample_contents)} 条示例教学内容")
        print("   请登录 Web 界面查看：http://localhost:5173/teaching")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 初始化失败：{e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🌱 开始初始化示例教学内容...")
    init_sample_contents()
