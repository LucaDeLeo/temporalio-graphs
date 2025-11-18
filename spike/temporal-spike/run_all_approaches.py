"""Run all three approaches and compare results."""
import asyncio
import sys

# Import all approaches
from approach1_simplified import run_approach1
from approach2_history_parsing import run_approach2
from approach3_static_analysis import run_approach3


async def main():
    """Run all approaches and display comparison."""
    print("\n" + "=" * 60)
    print("TEMPORAL GRAPH GENERATION - ARCHITECTURE SPIKE")
    print("Comparing Three Approaches")
    print("=" * 60 + "\n")

    results = {}

    # Run Approach 1
    try:
        paths1, mermaid1, time1 = await run_approach1()
        results['approach1'] = {
            'paths': len(paths1),
            'time': time1,
            'success': True
        }
    except Exception as e:
        print(f"\nApproach 1 failed: {e}")
        results['approach1'] = {'success': False}

    print("\n" + "=" * 60 + "\n")

    # Run Approach 2
    try:
        histories2, mermaid2, time2 = await run_approach2()
        results['approach2'] = {
            'paths': len(histories2),
            'time': time2,
            'success': True
        }
    except Exception as e:
        print(f"\nApproach 2 failed: {e}")
        results['approach2'] = {'success': False}

    print("\n" + "=" * 60 + "\n")

    # Run Approach 3
    try:
        paths3, mermaid3, time3 = await run_approach3()
        results['approach3'] = {
            'paths': len(paths3),
            'time': time3,
            'success': True
        }
    except Exception as e:
        print(f"\nApproach 3 failed: {e}")
        results['approach3'] = {'success': False}

    # Summary comparison
    print("\n" + "=" * 60)
    print("FINAL COMPARISON")
    print("=" * 60)

    print("\n{:<30} {:<15} {:<15} {:<15}".format(
        "Metric", "Approach 1", "Approach 2", "Approach 3"
    ))
    print("-" * 75)

    # Success
    print("{:<30} {:<15} {:<15} {:<15}".format(
        "Success",
        "✓" if results['approach1']['success'] else "✗",
        "✓" if results['approach2']['success'] else "✗",
        "✓" if results['approach3']['success'] else "✗"
    ))

    # Paths generated
    if all(r['success'] for r in results.values()):
        print("{:<30} {:<15} {:<15} {:<15}".format(
            "Paths Generated",
            str(results['approach1']['paths']),
            str(results['approach2']['paths']),
            str(results['approach3']['paths'])
        ))

        # Execution time
        print("{:<30} {:<15} {:<15} {:<15}".format(
            "Execution Time (s)",
            f"{results['approach1']['time']:.4f}",
            f"{results['approach2']['time']:.4f}",
            f"{results['approach3']['time']:.4f}"
        ))

    # Key capabilities
    print("\n{:<30} {:<15} {:<15} {:<15}".format(
        "Capability", "Approach 1", "Approach 2", "Approach 3"
    ))
    print("-" * 75)

    capabilities = [
        ("All Possible Paths", "Requires exec", "No", "Yes"),
        ("No Execution Needed", "No", "No", "Yes"),
        ("Matches .NET Model", "Partial", "No", "Yes"),
        ("Implementation Complexity", "Low", "Medium", "High"),
        ("Scalability (2^n)", "Poor", "Poor", "Good"),
    ]

    for capability, a1, a2, a3 in capabilities:
        print("{:<30} {:<15} {:<15} {:<15}".format(capability, a1, a2, a3))

    print("\n" + "=" * 60)
    print("RECOMMENDATION: Approach 3 (Static Code Analysis)")
    print("=" * 60)
    print("\nRationale:")
    print("  • Only approach that generates ALL possible paths")
    print("  • No workflow execution required")
    print("  • Matches .NET's permutation-based model")
    print("  • Excellent performance characteristics")
    print("  • Implementation complexity is manageable")
    print("\nSee findings.md for detailed analysis and next steps.")
    print()


if __name__ == "__main__":
    asyncio.run(main())
