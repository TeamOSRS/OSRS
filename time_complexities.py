import math
from typing import List

def constant_time_example(arr: List[int]) -> int:
    return arr[0] if arr else -1

def binary_search(arr: List[int], target: int) -> int:
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

def linear_search(arr: List[int], target: int) -> int:
    for i, value in enumerate(arr):
        if value == target:
            return i
    return -1

def merge_sort(arr: List[int]) -> List[int]:
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return _merge(left, right)

def _merge(left: List[int], right: List[int]) -> List[int]:
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged

def bubble_sort(arr: List[int]) -> List[int]:
    n = len(arr)
    result = arr.copy()
    for i in range(n):
        for j in range(0, n - i - 1):
            if result[j] > result[j + 1]:
                result[j], result[j + 1] = result[j + 1], result[j]
    return result

def count_triplets(arr: List[int]) -> int:
    n = len(arr)
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                count += 1
    return count

def fibonacci_recursive(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)

if __name__ == "__main__":
    sample = list(range(10))
    print("Constant time example:", constant_time_example(sample))
    print("Linear search (5):", linear_search(sample, 5))
    print("Binary search (5):", binary_search(sample, 5))
    print("Merge sort:", merge_sort([5, 2, 9, 1, 5, 6]))
    print("Bubble sort:", bubble_sort([5, 2, 9, 1, 5, 6]))
    print("Count triplets (n=5):", count_triplets([1, 2, 3, 4, 5]))
    print("Fibonacci recursive (n=6):", fibonacci_recursive(6))
