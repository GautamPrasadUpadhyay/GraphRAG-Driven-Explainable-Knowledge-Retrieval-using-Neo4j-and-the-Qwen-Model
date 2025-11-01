

import json
from neo4j import GraphDatabase

class LungCancerGraphLoader:
    def __init__(self, uri, user, password):
        """Initialize connection to Neo4j"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print("✓ Connected to Neo4j successfully!")
    
    def close(self):
        """Close the Neo4j connection"""
        self.driver.close()
        print("✓ Connection closed")
    
    def get_text(self, section, key='text'):
        """Helper function to get text with fallback to 'Text' or 'text'"""
        if 'text' in section:
            return section['text']
        elif 'Text' in section:
            return section['Text']
        return ""
    
    def clear_database(self):
        """Clear all existing data (use with caution!)"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("✓ Database cleared")
    
    def create_constraints(self):
        """Create uniqueness constraints for better performance"""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Paper) REQUIRE p.title IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Section) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Algorithm) REQUIRE a.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Metric) REQUIRE m.name IS UNIQUE"
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                session.run(constraint)
        print("✓ Constraints created")
    
    def load_paper_metadata(self, data):
        """Create the main research paper node"""
        query = """
        CREATE (p:Paper {
            file_path: $file_path,
            file_size: $file_size,
            page_count: $page_count,
            author: $author,
            creator: $creator,
            title: $title
        })
        RETURN p
        """
        
        with self.driver.session() as session:
            session.run(query, 
                file_path=data['file_path'],
                file_size=data['file_size_human'],
                page_count=data['page_count'],
                author=data['metadata']['author'],
                creator=data['metadata']['creator'],
                title=data['metadata'].get('title', 'Lung Cancer Detection using Supervised ML')
            )
        print("✓ Paper metadata loaded")
    
    def load_abstract(self, paper_data):
        """Load abstract section and its entities"""
        abstract = paper_data['Sections']['Abstract']
        text = self.get_text(abstract)
        
        # Create Abstract Section
        query = """
        MATCH (p:Paper)
        CREATE (s:Section:Abstract {
            name: 'Abstract',
            text: $text
        })
        CREATE (p)-[:HAS_SECTION]->(s)
        RETURN s
        """
        
        with self.driver.session() as session:
            session.run(query, text=text[:5000])  # Limit text length
        
        # Get entities
        entities = abstract.get('entities', abstract.get('Entities', {}))
        
        # Create ML Algorithms
        if 'ML Tools' in entities:
            algorithms = entities['ML Tools']
        elif 'Diagnostic Techniques' in entities:
            algorithms = entities['Diagnostic Techniques']
        else:
            algorithms = ['SVM', 'ANN', 'MLR', 'Random Forest']
        
        for algo in algorithms:
            query = """
            MATCH (s:Abstract)
            MERGE (a:Algorithm {name: $algo})
            CREATE (s)-[:MENTIONS_ALGORITHM]->(a)
            """
            with self.driver.session() as session:
                if isinstance(algo, str):
                    session.run(query, algo=algo)
        
        # Create Keywords if available
        keywords_text = entities.get('Keywords', entities.get('keywords', ''))
        if keywords_text and isinstance(keywords_text, str):
            keywords = [k.strip() for k in keywords_text.split(',')]
            for keyword in keywords[:10]:  # Limit to 10 keywords
                query = """
                MATCH (s:Abstract)
                MERGE (k:Keyword {name: $keyword})
                CREATE (s)-[:HAS_KEYWORD]->(k)
                """
                with self.driver.session() as session:
                    session.run(query, keyword=keyword)
        
        print("✓ Abstract section loaded")
    
    def load_introduction(self, paper_data):
        """Load introduction section with cancer types and symptoms"""
        intro = paper_data['Sections']['Introduction']
        text = self.get_text(intro)
        entities = intro.get('entities', intro.get('Entities', {}))
        
        # Create Introduction Section
        query = """
        MATCH (p:Paper)
        CREATE (s:Section:Introduction {
            name: 'Introduction',
            text: $text
        })
        CREATE (p)-[:HAS_SECTION]->(s)
        RETURN s
        """
        
        with self.driver.session() as session:
            session.run(query, text=text[:5000])  # Limit text length
        
        # Create Symptoms
        symptoms = entities.get('Symptoms', [])
        if isinstance(symptoms, str):
            symptoms = [s.strip() for s in symptoms.split(',')]
        
        for symptom in symptoms[:20]:  # Limit to 20
            query = """
            MATCH (s:Introduction)
            MERGE (sym:Symptom {name: $symptom})
            CREATE (s)-[:MENTIONS_SYMPTOM]->(sym)
            """
            with self.driver.session() as session:
                session.run(query, symptom=symptom.strip())
        
        # Create Cancer Types
        cancer_types = entities.get('Type of Cancer', entities.get('Types of Cancer', []))
        if isinstance(cancer_types, str):
            cancer_types = [c.strip() for c in cancer_types.split(',')]
        
        for cancer_type in cancer_types[:10]:  # Limit to 10
            query = """
            MATCH (s:Introduction)
            MERGE (c:CancerType {name: $cancer_type})
            CREATE (s)-[:DISCUSSES_CANCER_TYPE]->(c)
            """
            with self.driver.session() as session:
                session.run(query, cancer_type=str(cancer_type).strip()[:100])
        
        # Create Diagnostic Techniques
        techniques = entities.get('Common Diagnostic Techniques', [])
        if isinstance(techniques, str):
            techniques = [t.strip() for t in techniques.split(',')]
        
        for technique in techniques[:10]:
            query = """
            MATCH (s:Introduction)
            MERGE (t:Technique {name: $technique, type: 'diagnostic'})
            CREATE (s)-[:USES_TECHNIQUE]->(t)
            """
            with self.driver.session() as session:
                session.run(query, technique=technique.strip())
        
        # Create Risk Factors (Habits)
        habits = entities.get('Habits', [])
        if isinstance(habits, str):
            habits = [h.strip() for h in habits.split(',')]
        
        for habit in habits[:10]:
            query = """
            MATCH (s:Introduction)
            MERGE (r:RiskFactor {name: $habit})
            CREATE (s)-[:IDENTIFIES_RISK_FACTOR]->(r)
            """
            with self.driver.session() as session:
                session.run(query, habit=habit.strip())
        
        print("✓ Introduction section loaded")
    
    def load_methodology(self, paper_data):
        """Load methodology section with dataset and models"""
        methodology = paper_data['Sections'].get('Methodology', {})
        
        # Create Methodology Section
        method_text = self.get_text(methodology)
        query = """
        MATCH (p:Paper)
        CREATE (s:Section:Methodology {
            name: 'Methodology',
            text: $text
        })
        CREATE (p)-[:HAS_SECTION]->(s)
        RETURN s
        """
        
        with self.driver.session() as session:
            session.run(query, text=method_text[:5000])
        
        # Create Dataset node
        query = """
        MATCH (s:Methodology)
        CREATE (d:Dataset {
            name: 'Lung Cancer Dataset',
            source: 'data.world',
            format: 'CSV',
            instances: 1000,
            features: 24
        })
        CREATE (s)-[:USES_DATASET]->(d)
        RETURN d
        """
        
        with self.driver.session() as session:
            session.run(query)
        
        # Create Model nodes
        entities = methodology.get('Entities', methodology.get('entities', {}))
        models_list = entities.get('Proposed Models', [])
        
        if not models_list:
            models_list = [
                'Artificial Neural Network (ANN)',
                'Support Vector Machine (SVM)',
                'Random Forest',
                'Multiple Linear Regression (MLR)'
            ]
        
        for model_name in models_list:
            # Extract short name
            if '(' in model_name and ')' in model_name:
                short = model_name.split('(')[1].split(')')[0]
                full = model_name.split('(')[0].strip()
            else:
                short = model_name
                full = model_name
            
            query = """
            MATCH (s:Methodology)
            CREATE (m:Model:Algorithm {
                name: $name,
                full_name: $full_name,
                type: 'supervised'
            })
            CREATE (s)-[:IMPLEMENTS_MODEL]->(m)
            """
            with self.driver.session() as session:
                session.run(query, name=short, full_name=full)
 
        symptoms = entities.get('Symptoms', [])
        if isinstance(symptoms, str):
            symptoms = [s.strip() for s in symptoms.split(',')]
        
        for symptom in symptoms[:20]:
            query = """
            MATCH (d:Dataset)
            MERGE (f:Feature:Symptom {name: $symptom})
            CREATE (d)-[:HAS_FEATURE]->(f)
            """
            with self.driver.session() as session:
                session.run(query, symptom=symptom.strip())
        
        print("✓ Methodology section loaded")
    
    def load_results(self, paper_data):
        """Load results with model performance metrics"""
        results = paper_data['Sections'].get('Results', {})
        
        results_text = self.get_text(results)
        query = """
        MATCH (p:Paper)
        CREATE (s:Section:Results {
            name: 'Results',
            text: $text
        })
        CREATE (p)-[:HAS_SECTION]->(s)
        RETURN s
        """
        
        with self.driver.session() as session:
            session.run(query, text=results_text[:5000])
        
        performances = [
            {'model': 'ANN', 'accuracy': 65.75},
            {'model': 'MLR', 'accuracy': 77.52},
            {'model': 'RF', 'accuracy': 99.99},
            {'model': 'SVM', 'accuracy': 98.91}
        ]
        
        for perf in performances:
            query = """
            MATCH (m:Model)
            WHERE m.name CONTAINS $model OR m.full_name CONTAINS $model
            MATCH (s:Results)
            CREATE (r:Result {
                accuracy: $accuracy,
                metric: 'Accuracy (%)',
                evaluated_on: 'Test Set'
            })
            CREATE (m)-[:HAS_RESULT]->(r)
            CREATE (s)-[:CONTAINS_RESULT]->(r)
            """
            with self.driver.session() as session:
                session.run(query, model=perf['model'], accuracy=perf['accuracy'])
        

        query = """
        MATCH (m:Model)
        WHERE m.name CONTAINS 'Forest' OR m.full_name CONTAINS 'Forest'
        MATCH (p:Paper)
        CREATE (p)-[:BEST_MODEL]->(m)
        """
        with self.driver.session() as session:
            session.run(query)
        
        print("✓ Results section loaded")
    
    def load_conclusion(self, paper_data):
        """Load conclusion section"""
        conclusion = paper_data['Sections'].get('Conclusion', {})
        text = self.get_text(conclusion)
        
        query = """
        MATCH (p:Paper)
        CREATE (s:Section:Conclusion {
            name: 'Conclusion',
            text: $text
        })
        CREATE (p)-[:HAS_SECTION]->(s)
        RETURN s
        """
        
        with self.driver.session() as session:
            session.run(query, text=text[:5000])
        
        print("✓ Conclusion section loaded")
    
    def create_relationships(self):
        """Create additional meaningful relationships"""
        
   
        query = """
        MATCH (s:Symptom)
        MATCH (c:CancerType)
        WHERE c.name CONTAINS 'lung' OR c.name CONTAINS 'Lung'
        CREATE (s)-[:INDICATES]->(c)
        """
        with self.driver.session() as session:
            session.run(query)
        
        query = """
        MATCH (r:RiskFactor)
        MATCH (c:CancerType)
        WHERE c.name CONTAINS 'lung' OR c.name CONTAINS 'Lung'
        CREATE (r)-[:INCREASES_RISK_OF]->(c)
        """
        with self.driver.session() as session:
            session.run(query)
        
        print("✓ Additional relationships created")
    
    def load_all_data(self, json_file):
        """Main method to load all data from JSON file"""
        print("\n🚀 Starting data load process...")
        
   
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("✓ JSON file loaded")
        
        # Clear existing data
        self.clear_database()
        
        # Create constraints
        self.create_constraints()
        
        # Load all sections
        try:
            self.load_paper_metadata(data)
            self.load_abstract(data)
            self.load_introduction(data)
            self.load_methodology(data)
            self.load_results(data)
            self.load_conclusion(data)
            self.create_relationships()
        except Exception as e:
            print(f"⚠️ Error during loading: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        
        print("\n✅ All data loaded successfully!")
        print("\n📊 Graph Statistics:")
        self.print_statistics()
    
    def print_statistics(self):
        """Print graph statistics"""
        queries = {
            "Total Nodes": "MATCH (n) RETURN count(n) as count",
            "Total Relationships": "MATCH ()-[r]->() RETURN count(r) as count",
            "Node Types": "MATCH (n) RETURN labels(n)[0] as type, count(*) as count ORDER BY count DESC"
        }
        
        with self.driver.session() as session:
            for stat_name, query in queries.items():
                result = session.run(query)
                if stat_name == "Node Types":
                    print(f"\n{stat_name}:")
                    for record in result:
                        print(f"  - {record['type']}: {record['count']}")
                else:
                    count = result.single()['count']
                    print(f"{stat_name}: {count}")


if __name__ == "__main__":
    print("="*60)
    print("  Lung Cancer Research - Neo4j Knowledge Graph Loader")
    print("="*60)
    
   
    NEO4J_URI = "neo4j://127.0.0.1:7687" 
    NEO4J_USER = "neo4j" 
    NEO4J_PASSWORD = "12345678"  
    JSON_FILE = "blueprint_class.json"  
    
    loader = LungCancerGraphLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
       
        loader.load_all_data(JSON_FILE)
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
    finally:
       
        loader.close()
    
    print("\n" + "="*60)
    print("  You can now open Neo4j Browser to explore the graph!")
    print("  URL: http://localhost:7474")
    print("="*60)