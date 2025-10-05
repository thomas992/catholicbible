# DRB & CPDV Bible JSON

This repository provides structured JSON versions of two complete Catholic Bible translations:

- **Douay–Rheims Bible (DRB)**
- **Catholic Public Domain Version (CPDV)**

Each translation has been normalized into a unified schema for ease of use in web and application projects.

## Format

Both JSON files share the same structure:

```json
{
  "books": [
    {
      "name": "Genesis",
      "chapters": [
        {
          "number": 1,
          "verses": [
            { "number": 1, "text": "In the beginning, God created heaven and earth." },
            { "number": 2, "text": "And the earth was void and empty, ..." }
          ]
        }
      ]
    }
  ]
}
````

* **books**: Ordered array of all canonical books.
* **chapters**: Each book contains numbered chapters.
* **verses**: Each chapter contains an array of verses with number and text.

## Usage

* Ideal for Bible search engines, comparison tools, or personal study apps.
* The JSON is human-readable and easy to parse in most programming languages.
* Both DRB and CPDV are in the public domain.

## Attribution

Prepared and structured by **Thomas Hansen**.
Translations are in the **public domain** and free to use without restriction.

## License

This repository is dedicated to the public domain under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).
