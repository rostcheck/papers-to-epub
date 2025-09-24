#!/usr/bin/env python3
import json
import jsonschema
from pathlib import Path

def validate_academic_paper(json_file, schema_file):
    """Validate academic paper JSON against schema"""
    
    # Load schema
    with open(schema_file, 'r') as f:
        schema = json.load(f)
    
    # Load document
    with open(json_file, 'r') as f:
        document = json.load(f)
    
    try:
        # Validate
        jsonschema.validate(document, schema)
        print(f"✅ {json_file} is valid according to schema")
        return True
    except jsonschema.ValidationError as e:
        print(f"❌ Validation error in {json_file}:")
        print(f"   Path: {' -> '.join(str(p) for p in e.absolute_path)}")
        print(f"   Error: {e.message}")
        return False
    except jsonschema.SchemaError as e:
        print(f"❌ Schema error: {e.message}")
        return False

def main():
    """Test schema validation"""
    schema_file = "academic_paper_schema.json"
    test_file = "word2vec_structured.json"
    
    if not Path(schema_file).exists():
        print(f"❌ Schema file not found: {schema_file}")
        return
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    print("🔍 Validating Word2Vec paper against academic paper schema...")
    print("=" * 60)
    
    is_valid = validate_academic_paper(test_file, schema_file)
    
    if is_valid:
        print("\n🎉 Schema validation successful!")
        print("The Word2Vec structured JSON conforms to our academic paper schema.")
    else:
        print("\n⚠️ Schema validation failed.")
        print("The JSON structure needs adjustments to match the schema.")

if __name__ == "__main__":
    main()
