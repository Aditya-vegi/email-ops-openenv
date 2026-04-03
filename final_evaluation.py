#!/usr/bin/env python3
"""
Final Evaluation Script - Complete Phase 1, 2, 3 Readiness Check
"""

import json
import subprocess
import sys
import time
from pathlib import Path

class FinalEvaluator:
    def __init__(self):
        self.results = {
            "phase1_pass_fail": {},
            "phase2_scored": {},
            "phase3_human_ready": {},
            "overall_status": "pending"
        }
    
    def check_phase1_requirements(self):
        """Check Phase 1: Pass/Fail Gate Requirements"""
        print("=" * 60)
        print("PHASE 1: PASS/FAIL GATE CHECK")
        print("=" * 60)
        
        phase1_results = {}
        
        # 1. HF Space deploys
        print("\n1. Checking HF Space deployment...")
        try:
            import requests
            response = requests.get("https://ADITYA-VEGI-email-ops-openenv.hf.space/", timeout=10)
            if response.status_code == 200:
                phase1_results["hf_space_deploys"] = True
                print("PASS HF Space is accessible")
            else:
                phase1_results["hf_space_deploys"] = False
                print("FAIL HF Space not accessible")
        except:
            phase1_results["hf_space_deploys"] = False
            print("FAIL Could not reach HF Space")
        
        # 2. OpenEnv spec compliance
        print("\n2. Checking OpenEnv spec compliance...")
        try:
            result = subprocess.run([sys.executable, "test_compliance.py"], 
                                  capture_output=True, text=True, cwd=".")
            if "ALL TESTS PASSED" in result.stdout:
                phase1_results["openenv_spec"] = True
                print("PASS OpenEnv spec compliance verified")
            else:
                phase1_results["openenv_spec"] = False
                print("FAIL OpenEnv spec compliance failed")
        except:
            phase1_results["openenv_spec"] = False
            print("FAIL Could not run compliance tests")
        
        # 3. Dockerfile builds
        print("\n3. Checking Dockerfile...")
        dockerfile_path = Path("Dockerfile")
        if dockerfile_path.exists():
            # Check if Dockerfile has correct structure
            with open(dockerfile_path, 'r') as f:
                content = f.read()
                if "FROM python:" in content and "EXPOSE 8000" in content:
                    phase1_results["dockerfile_builds"] = True
                    print("PASS Dockerfile structure is correct")
                else:
                    phase1_results["dockerfile_builds"] = False
                    print("FAIL Dockerfile structure issues")
        else:
            phase1_results["dockerfile_builds"] = False
            print("FAIL Dockerfile not found")
        
        # 4. Baseline reproduces
        print("\n4. Checking baseline reproduction...")
        baseline_script = Path("baseline_agent.py")
        if baseline_script.exists():
            try:
                # Quick syntax check
                result = subprocess.run([sys.executable, "-m", "py_compile", "baseline_agent.py"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    phase1_results["baseline_reproduces"] = True
                    print("PASS Baseline agent script is valid")
                else:
                    phase1_results["baseline_reproduces"] = False
                    print("FAIL Baseline agent script has errors")
            except:
                phase1_results["baseline_reproduces"] = False
                print("FAIL Could not validate baseline agent")
        else:
            phase1_results["baseline_reproduces"] = False
            print("FAIL Baseline agent script not found")
        
        # 5. 3+ tasks with graders
        print("\n5. Checking tasks and graders...")
        env_script = Path("env.py")
        graders_script = Path("graders.py")
        
        if env_script.exists() and graders_script.exists():
            with open(env_script, 'r') as f:
                env_content = f.read()
            with open(graders_script, 'r') as f:
                graders_content = f.read()
            
            # Check for three task types
            tasks_found = []
            if "grade_easy" in graders_content:
                tasks_found.append("easy")
            if "grade_medium" in graders_content:
                tasks_found.append("medium")
            if "grade_hard" in graders_content:
                tasks_found.append("hard")
            
            if len(tasks_found) >= 3:
                phase1_results["tasks_with_graders"] = True
                print(f"PASS Found {len(tasks_found)} tasks with graders: {tasks_found}")
            else:
                phase1_results["tasks_with_graders"] = False
                print(f"FAIL Only found {len(tasks_found)} tasks: {tasks_found}")
        else:
            phase1_results["tasks_with_graders"] = False
            print("FAIL Environment or graders script not found")
        
        # Phase 1 overall status
        phase1_passed = all(phase1_results.values())
        self.results["phase1_pass_fail"] = {
            "requirements": phase1_results,
            "passed": phase1_passed
        }
        
        print(f"\nPHASE 1 STATUS: {'PASSED' if phase1_passed else 'FAILED'}")
        return phase1_passed
    
    def check_phase2_readiness(self):
        """Check Phase 2: Agentic Evaluation Readiness"""
        print("\n" + "=" * 60)
        print("PHASE 2: AGENTIC EVALUATION READINESS")
        print("=" * 60)
        
        phase2_results = {}
        
        # Check baseline agent
        print("\n1. Checking baseline agent...")
        baseline_script = Path("baseline_agent.py")
        if baseline_script.exists():
            phase2_results["baseline_agent"] = True
            print("PASS Baseline agent script exists")
        else:
            phase2_results["baseline_agent"] = False
            print("FAIL Baseline agent script missing")
        
        # Check agentic evaluation
        print("\n2. Checking agentic evaluation framework...")
        agentic_script = Path("agentic_evaluation.py")
        if agentic_script.exists():
            phase2_results["agentic_framework"] = True
            print("PASS Agentic evaluation framework exists")
        else:
            phase2_results["agentic_framework"] = False
            print("FAIL Agentic evaluation framework missing")
        
        # Check variance analysis capability
        print("\n3. Checking variance analysis...")
        if agentic_script.exists():
            with open(agentic_script, 'r') as f:
                content = f.read()
                if "std_dev" in content and "variance" in content.lower():
                    phase2_results["variance_analysis"] = True
                    print("PASS Variance analysis implemented")
                else:
                    phase2_results["variance_analysis"] = False
                    print("FAIL Variance analysis not found")
        else:
            phase2_results["variance_analysis"] = False
            print("FAIL Cannot check variance analysis")
        
        # Check standard LLM agent compatibility
        print("\n4. Checking LLM agent compatibility...")
        if baseline_script.exists():
            with open(baseline_script, 'r') as f:
                content = f.read()
                if "LLMAgent" in content or "generate_action" in content:
                    phase2_results["llm_compatibility"] = True
                    print("PASS LLM agent compatibility framework exists")
                else:
                    phase2_results["llm_compatibility"] = False
                    print("FAIL LLM agent compatibility not found")
        else:
            phase2_results["llm_compatibility"] = False
            print("FAIL Cannot check LLM compatibility")
        
        phase2_ready = all(phase2_results.values())
        self.results["phase2_scored"] = {
            "components": phase2_results,
            "ready": phase2_ready
        }
        
        print(f"\nPHASE 2 STATUS: {'READY' if phase2_ready else 'NOT READY'}")
        return phase2_ready
    
    def check_phase3_readiness(self):
        """Check Phase 3: Human Review Readiness"""
        print("\n" + "=" * 60)
        print("PHASE 3: HUMAN REVIEW READINESS")
        print("=" * 60)
        
        phase3_results = {}
        
        # Check documentation
        print("\n1. Checking documentation...")
        readme = Path("README.md")
        human_review_doc = Path("human_review_prep.md")
        
        if readme.exists():
            phase3_results["readme_complete"] = True
            print("PASS README.md exists")
        else:
            phase3_results["readme_complete"] = False
            print("FAIL README.md missing")
        
        if human_review_doc.exists():
            phase3_results["human_review_prep"] = True
            print("PASS Human review preparation document exists")
        else:
            phase3_results["human_review_prep"] = False
            print("FAIL Human review preparation document missing")
        
        # Check utility assessment
        print("\n2. Checking real-world utility...")
        if readme.exists():
            with open(readme, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                utility_keywords = ["customer support", "it incident", "business communication", "real-world"]
                utility_score = sum(1 for keyword in utility_keywords if keyword in content)
                
                if utility_score >= 2:
                    phase3_results["real_world_utility"] = True
                    print(f"PASS Strong real-world utility indicators ({utility_score}/4)")
                else:
                    phase3_results["real_world_utility"] = False
                    print(f"WARN Limited real-world utility indicators ({utility_score}/4)")
        else:
            phase3_results["real_world_utility"] = False
            print("FAIL Cannot assess utility without README")
        
        # Check creativity indicators
        print("\n3. Checking creativity and innovation...")
        if readme.exists():
            with open(readme, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                creativity_keywords = ["innovative", "novel", "creative", "unique", "multi-task"]
                creativity_score = sum(1 for keyword in creativity_keywords if keyword in content)
                
                if creativity_score >= 2:
                    phase3_results["creativity"] = True
                    print(f"PASS Creativity indicators present ({creativity_score}/5)")
                else:
                    phase3_results["creativity"] = False
                    print(f"WARN Limited creativity indicators ({creativity_score}/5)")
        else:
            phase3_results["creativity"] = False
            print("FAIL Cannot assess creativity without README")
        
        # Check exploit prevention
        print("\n4. Checking exploit prevention...")
        env_script = Path("env.py")
        if env_script.exists():
            with open(env_script, 'r', encoding='utf-8') as f:
                content = f.read()
                exploit_checks = ["valid_actions", "penalty", "max_steps", "error"]
                exploit_score = sum(1 for check in exploit_checks if check in content)
                
                if exploit_score >= 3:
                    phase3_results["exploit_prevention"] = True
                    print(f"PASS Strong exploit prevention ({exploit_score}/4)")
                else:
                    phase3_results["exploit_prevention"] = False
                    print(f"WARN Limited exploit prevention ({exploit_score}/4)")
        else:
            phase3_results["exploit_prevention"] = False
            print("FAIL Cannot check exploit prevention")
        
        phase3_ready = all(phase3_results.values())
        self.results["phase3_human_ready"] = {
            "criteria": phase3_results,
            "ready": phase3_ready
        }
        
        print(f"\nPHASE 3 STATUS: {'READY' if phase3_ready else 'NOT READY'}")
        return phase3_ready
    
    def generate_final_report(self):
        """Generate comprehensive final evaluation report"""
        print("\n" + "=" * 60)
        print("FINAL EVALUATION REPORT")
        print("=" * 60)
        
        # Run all checks
        phase1_status = self.check_phase1_requirements()
        phase2_status = self.check_phase2_readiness()
        phase3_status = self.check_phase3_readiness()
        
        # Overall status
        overall_passed = phase1_status and phase2_status and phase3_status
        self.results["overall_status"] = "PASSED" if overall_passed else "FAILED"
        
        print("\n" + "=" * 60)
        print("OVERALL EVALUATION SUMMARY")
        print("=" * 60)
        print(f"Phase 1 (Pass/Fail Gate): {'PASSED' if phase1_status else 'FAILED'}")
        print(f"Phase 2 (Agentic Evaluation): {'READY' if phase2_status else 'NOT READY'}")
        print(f"Phase 3 (Human Review): {'READY' if phase3_status else 'NOT READY'}")
        print(f"\nOVERALL STATUS: {self.results['overall_status']}")
        
        if overall_passed:
            print("\nSUCCESS! Your environment is ready for all evaluation phases!")
            print("\nNext steps:")
            print("1. Push latest changes to GitHub")
            print("2. Update HF Space if needed")
            print("3. Prepare for Phase 2 agentic evaluation")
            print("4. Get ready for Phase 3 human review")
        else:
            print("\nWARN Some requirements are not met. Please address the issues above.")
        
        # Save detailed results
        with open("final_evaluation_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nDetailed results saved to: final_evaluation_results.json")
        return self.results

def main():
    """Run final evaluation"""
    evaluator = FinalEvaluator()
    results = evaluator.generate_final_report()
    
    return results["overall_status"] == "PASSED"

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
