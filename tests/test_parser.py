from parser import parsefile


def test_parsefile():
    def check_start_end(file, start, end):
        text = parsefile(file)
        assert text.startswith(start)
        assert text.endswith(end)

    check_start_end(
        file="samples/number_system.json",
        start="rational number in mathematics . A number system is a state of numbers together with one or more operations such",
        end="the 4th line , we have to put years in the first two and no in the last one ."
    )

    check_start_end(
        file="samples/Basic Math - Lesson 1 - Complex Numbers.json",
        start=". that number on a number line . It's not real",
        end="For example , the square root of negative two for example , I cannot put",
    )
