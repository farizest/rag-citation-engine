"""
Sanity tests for retrieve.py.

These confirm the vector store is populated and basic retrieval works
correctly on an "easy" question -- one with a clear, unambiguous answer
that should retrieve its source page as the top result.

Requires the vector store to already exist (run src/embed.py first).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from retrieve import retrieve, load_collection


def test_collection_is_populated():
    collection = load_collection()
    count = collection.count()
    print(f"Collection has {count} vectors")
    assert count == 90, f"expected 90 chunks, found {count}"
    print("PASS: collection has the expected number of vectors\n")


def test_easy_question_retrieves_correct_top_result():
    results = retrieve("how many weeks of parental leave do we get?", k=5)

    assert len(results) == 5, "expected 5 results"

    top_result = results[0]
    print(f"Top result: {top_result['metadata']['page_title']} "
          f"(distance={top_result['distance']:.3f})")

    assert top_result["metadata"]["source_file"] == "hr\\parental-leave-policy.md" \
        or top_result["metadata"]["source_file"] == "hr/parental-leave-policy.md", \
        f"expected parental-leave-policy.md as top result, got {top_result['metadata']['source_file']}"

    print("PASS: easy question correctly retrieves its source page\n")


def test_results_are_sorted_by_distance():
    results = retrieve("how many weeks of parental leave do we get?", k=5)
    distances = [r["distance"] for r in results]

    print(f"Distances: {distances}")
    assert distances == sorted(distances), \
        "results should be sorted by ascending distance (closest first)"

    print("PASS: results are correctly sorted by distance\n")


if __name__ == "__main__":
    test_collection_is_populated()
    test_easy_question_retrieves_correct_top_result()
    test_results_are_sorted_by_distance()
    print("All retrieve tests passed.")