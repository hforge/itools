

#include <stdio.h>
#include <stdlib.h>

#include "../xml/parser.h"


int
main(int argc, char *argv[])
{
    char *filename;
    FILE *test_file;
    int nb_repeat;
    Parser *parser;
    Event event;

    /* Check input paramaters. */
    if (argc != 3)
        return 1;

    /* Get input parameters. */
    filename = argv[1];
    nb_repeat = atoi(argv[2]);

    /* Open the test file. */
    test_file = fopen(filename, "r");

    /* Loop. */
    for (; nb_repeat > 0; nb_repeat--)
    {
        /* Parse. */
        parser = parser_new(NULL, test_file);
        while (parser_next(parser, &event) == 0) {
            if (event.type == END_DOCUMENT)
                break;
            if (event.type == START_ELEMENT);
            else if (event.type == END_ELEMENT);
        }
        parser_free(parser);
        /* Again. */
        fseek(test_file, 0, SEEK_SET);
    }

    /* Ok */
    fclose(test_file);
    return 0;
}

