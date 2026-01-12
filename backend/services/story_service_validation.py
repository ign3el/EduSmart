    def _validate_story_json(self, story_json: dict) -> tuple[bool, list[str]]:
        """Comprehensive validation of story JSON structure.
        
        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []
        
        # Required top-level fields
        required_fields = ["title", "description", "grade_level", "subject", "learning_outcome", "scenes", "quiz"]
        for field in required_fields:
            if field not in story_json:
                errors.append(f"Missing required field: {field}")
        
        # Validate scenes
        if "scenes" in story_json:
            scenes = story_json["scenes"]
            if not isinstance(scenes, list):
                errors.append("'scenes' must be an array")
            elif len(scenes) == 0:
                errors.append("'scenes' array is empty - must have at least 1 scene")
            else:
                for i, scene in enumerate(scenes):
                    scene_num = i + 1
                    # Required scene fields
                    required_scene_fields = ["scene_number", "narrative_text", "image_prompt", "check_for_understanding"]
                    for field in required_scene_fields:
                        if field not in scene:
                            errors.append(f"Scene {scene_num}: Missing '{field}'")
                        elif not scene.get(field):  # Check if empty
                            errors.append(f"Scene {scene_num}: '{field}' is empty")
                    
                    # Validate scene_number sequence
                    if "scene_number" in scene and scene["scene_number"] != scene_num:
                        errors.append(f"Scene {scene_num}: scene_number mismatch (expected {scene_num}, got {scene['scene_number']})")
        
        # Validate quiz
        if "quiz" in story_json:
            quiz = story_json["quiz"]
            if not isinstance(quiz, list):
                errors.append("'quiz' must be an array")
            elif len(quiz) < 10:
                errors.append(f"'quiz' must have at least 10 questions (found {len(quiz)})")
            else:
                for i, question in enumerate(quiz):
                    q_num = i + 1
                    # Required quiz fields
                    required_quiz_fields = ["question_number", "question_text", "options", "correct_answer", "explanation"]
                    for field in required_quiz_fields:
                        if field not in question:
                            errors.append(f"Quiz Q{q_num}: Missing '{field}'")
                    
                    # Validate options
                    if "options" in question:
                        options = question["options"]
                        if not isinstance(options, list):
                            errors.append(f"Quiz Q{q_num}: 'options' must be an array")
                        elif len(options) != 4:
                            errors.append(f"Quiz Q{q_num}: Must have exactly 4 options (found {len(options)})")
                    
                    # Validate correct_answer
                    if "correct_answer" in question:
                        answer = question["correct_answer"]
                        if answer not in ["A", "B", "C", "D"]:
                            errors.append(f"Quiz Q{q_num}: correct_answer must be A, B, C, or D (got '{answer}')")
        
        return (len(errors) == 0, errors)
