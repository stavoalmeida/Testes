def primeiros_10_fibonacci() -> list[int]:
    """Retorna os primeiros 10 números da sequência de Fibonacci."""
    sequencia = []
    a, b = 0, 1

    for _ in range(10):
        sequencia.append(a)
        a, b = b, a + b

    return sequencia


if __name__ == "__main__":
    print(primeiros_10_fibonacci())
