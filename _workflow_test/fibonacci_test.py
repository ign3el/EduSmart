def generate_fibonacci(n):
    """
    Generates the first n Fibonacci numbers.
    Sequence starts: 0, 1, 1, 2, ...
    """
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    fib_sequence = [0, 1]
    
    while len(fib_sequence) < n:
        next_val = fib_sequence[-1] + fib_sequence[-2]
        fib_sequence.append(next_val)
        
    return fib_sequence

if __name__ == "__main__":
    count = 10
    fib_numbers = generate_fibonacci(count)
    
    print(f"First {count} Fibonacci numbers:")
    for num in fib_numbers:
        print(num)
