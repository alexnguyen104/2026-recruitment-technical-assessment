from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	name: str

@dataclass
class RequiredItem():
	name: str
	quantity: int

@dataclass
class Recipe(CookbookEntry):
	required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
	cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook = []

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str) -> Union[str , None]:
	# Replacing hyphens and underscores
	recipeName = recipeName.replace('-', ' ')
	recipeName = recipeName.replace('_', ' ')

	# Check for other characters
	for letter in recipeName:
		if not letter.isalpha() and letter != ' ':
			recipeName = recipeName.replace(letter, '')
	
	# Capitalising letters
	recipeName = recipeName.title()

	# One whitespace
	recipeName = recipeName.strip()
	recipeName = " ".join(recipeName.split())

	# Check length
	if len(recipeName) == 0:
		return None
	
	return recipeName

# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
	data = request.get_json()
	data["name"] = parse_handwriting(data["name"])

	global cookbook
	if not is_unique(data, cookbook):
		return '', 400

	if data["type"] == "recipe":
		if not is_recipe_valid(data):
			return '', 400

	elif data["type"] == "ingredient":
		if not is_ingredient_valid(data):
			return '', 400
	else:
		return '', 400
	
	# Update to cookbook
	cookbook.append(data)
	
	return '', 200

def is_unique(data, cookbook):
	for entry in cookbook:
		if entry["name"] == data["name"]:
			return False
	return True

def is_recipe_valid(data):
	if "cookTime" in data:
		return False

	# Check if ingredient is duplicated
	for i in range(len(data["requiredItems"]) - 1):
		item = data["requiredItems"]
		if item[i]["name"] == item[i + 1]["name"]:
			return False
		
	return True

def is_ingredient_valid(data):
	if "requiredItems" in data:
		return False
	
	if data["cookTime"] < 0:
		return False
	
	return True

# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route('/summary', methods=['GET'])
def summary():
	global cookbook
	name = request.args.get("name")
	name = parse_handwriting(name)

	# Check if the recipe's name exists and the recipe's items exist in the cookbook
	if not recipe_name_exists(name, cookbook) or not items_exist(name,cookbook):
		return '', 400
	
	base_ingredient, cook_time = get_base_ingredient(name, cookbook)

	recipe_summary = {
		"name": name,
		"cookTime": cook_time,
		"ingredients": base_ingredient
	}

	return jsonify(recipe_summary), 200

def recipe_name_exists(name, cookbook):
	for entry in cookbook:
		if entry["name"] == name and entry["type"] == "recipe":
			return True
		
	return False

def get_cookbook_index_by_name(name, cookbook):
	index = None
	for i, entry in enumerate(cookbook):
		if entry["name"] == name:
			index = i
	
	return index

def items_exist(name, cookbook):
	index = get_cookbook_index_by_name(name, cookbook)

	for item in cookbook[index]["requiredItems"]:
		for entry in cookbook:
			if item["name"] == entry["name"]:
				return True
			
	return False

def get_base_ingredient_raw(name, parent_quantity, cookbook):
	ingredient_list_raw = []
	index = get_cookbook_index_by_name(name, cookbook)

	for item in cookbook[index]["requiredItems"]:
		item_index = get_cookbook_index_by_name(item["name"], cookbook)

		if cookbook[item_index]["type"] == "ingredient":
			ingredient = {
				"name": item["name"],
				"quantity": item["quantity"] * parent_quantity,
				"cookTime": cookbook[item_index]["cookTime"]
			}
			ingredient_list_raw.append(ingredient)
		else:
			ingredient_list_raw.extend(get_base_ingredient_raw(item["name"], item["quantity"], cookbook))

	return ingredient_list_raw
			
def get_base_ingredient(name, cookbook):
	raw_list = get_base_ingredient_raw(name, 1, cookbook)
	edited_list = []
	index_of_added_ingredient = []
	cook_time = get_cook_time(raw_list)

	for i in range(len(raw_list)):
		quantity = raw_list[i]["quantity"]
		
		# Check if the ingredient is already added to the edited_list
		if i in index_of_added_ingredient:
			continue

		# Update the quantity for the duplicated ingredients
		index_of_added_ingredient.append(i)
		for j in range(len(raw_list)):
			if raw_list[i]["name"] == raw_list[j]["name"] and i != j:
				quantity += raw_list[j]["quantity"]
				index_of_added_ingredient.append(j)

		ingredient = {
			"name": raw_list[i]["name"],
			"quantity": quantity
		}

		edited_list.append(ingredient)

	return edited_list, cook_time

def get_cook_time(raw_list):
	cook_time = 0
	for i in range(len(raw_list)):
		cook_time += raw_list[i]["cookTime"] * raw_list[i]["quantity"]
		
	return cook_time
	
# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)
