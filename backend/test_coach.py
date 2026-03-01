from agent_core import get_strategic_coaching

code = """
def twoSum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
"""

problem = "Find two numbers in an array that add up to target."

# This should print the "CoachingTip" JSON
print(get_strategic_coaching(code, problem))