 # Function for the calculator
def calculate():
    print("\n--- Calculator ---")
    num1 = float(input("Enter the first number: "))
    num2 = float(input("Enter the second number: "))
    operation = input("Choose operation (+, -, *, /): ")

    if operation == "+":
        result = num1 + num2
    elif operation == "-":
        result = num1 - num2
    elif operation == "*":
        result = num1 * num2
    elif operation == "/":
        if num2 != 0:
            result = num1 / num2
        else:
            print("Error: Cannot divide by zero.")
            return
    else:
        print("Invalid operation.")
        return

    print("Result:", result)

# Function for the mad lingo game
def mad_game():
    print("\n--- Mad Lingo Game ---")
    name = input("Enter a name: ")
    place = input("Enter a place: ")
    adjective = input("Enter an adjective: ")

    print(f"\nStory: One day, {name} flew to {place} and found a {adjective} alien pet!")

# Main program
print("Welcome to Rider’s Smart App!")
user_name = input("What's your name? ")
print(f"Hi {user_name}!")

print("\nWhat would you like to do?")
print("1 - Use Calculator")
print("2 - Play Mad Lingo Game")

choice = input("Enter 1 or 2: ")

if choice == "1":
    calculate()
elif choice == "2":
    mad_game()
else:
    print("Invalid option. Try again.") 