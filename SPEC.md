# De La Salle University
**Computer Technology Department**
**CSC611M**

## Distributed Programming Project – Website Crawler

### Description
Organizations use websites to disseminate information to potential customers or partners. This also makes their data accessible to search engines and large language models (LLMs), which rely on web crawlers to navigate websites and extract relevant information. Through this process, an organization’s content becomes discoverable in search queries and prompt-generated responses.

A web crawler is an automated tool that recursively accesses web pages and extracts hyperlinks to explore a website or the internet as a whole. Given the vast number of pages available online, web crawlers are often implemented using parallel programming techniques to improve efficiency and performance.

### Project Requirement
The following are the requirements for the project:

*   Create a web crawler application that automatically finds and collects URLs from a given website within a specified amount of time
    *   **Input arguments of the program:**
        *   URL of the website to be crawled
        *   Duration that the web crawler will run (in minutes)
        *   Number of nodes that will be used
    *   **Output of the program:**
        *   CSV file of extracted URLs with their respective descriptions (e.g. title or label). Each URL should only be listed once, even if it appears in multiple pages.
        *   Text file containing the number of pages crawled, number of URLs found, and a list of all unique URLs accessed
*   **Website for crawling:** `https://www.dlsu.edu.ph`
    *   Do not use other websites
*   **Program implementation:**
    *   Program can be implemented using Python, C++ or Java
    *   Any middleware API and OS platform (Linux is suggested) can be used
    *   Program or system should use at least two machines (physical or virtual) or containers in different VMs
    *   Program implementation should use distributed system-based techniques like coordination, ensuring transaction synchronization, message passing
    *   Program implementation can use libraries or APIs that does web page retrieval
        *   Examples: BeautifulSoup, lxml, html.parser
        *   Libraries or APIs that does the web crawling automatically are not allowed

---

### Project Rubrics
The project is to be graded using the following criteria / rubric:

| CRITERIA | EXEMPLARY (4) | SATISFACTORY (3) | DEVELOPING (2) | BEGINNING (1) |
| :--- | :--- | :--- | :--- | :--- |
| **Technical Documentation**<br>(10%) | Document has presented the architecture of the system, pointed out the concepts, has given an excellent analysis of the performance of the system and provided a conclusion. | Document has presented the architecture of the system, pointed out the concepts, has given simple analysis of the performance of the system. | Document has presented the architecture of the system and pointed out the concepts. | No documentation |
| **Distributed Techniques**<br>(40%) | Multiple machines or containers are used to distribute workload by using synchronization or parallel techniques | Multiple machines or containers are used but workload was not distributed nor use parallel techniques | Program essentially uses a single machine (not using VMs or containers) | No program submitted |
| **Performance**<br>(50%) | Project is able to achieve task and result of task is consistent | | Project is able to achieve required task but not done in parallel manner or result is not consistent | Project is not working |

### Documentation
Documentation requirements for the project is as follows:

*   Document should have the outline:
    1.  **Introduction**
        *   Give a brief discussion of the project and its requirement
    2.  **Program Implementation**
        *   Discussion on how the program was implemented
            *   Use of distributed system APIs
            *   Sharing of data between processes whether it is within or in different nodes
            *   Distributed systems techniques used for coordination, message passing, and others
    3.  **Result**
        *   Discussion of the results
        *   Explanation or analysis why such results was achieved
    4.  **Conclusion**
        *   Discuss briefly how distributed system techniques was used
        *   Discuss how distributed system techniques improved (or not improved) performance
    5.  **References**
        *   References used for concepts, programming techniques or libraries used
*   Document is to follow the IEEE manuscript template for conference proceeding
    *   Format for the manuscript is found at: [IEEE - Manuscript Templates for Conference Proceedings](https://www.ieee.org/conferences/publishing/templates.html)

---

### Submission Requirements
For submission:
*   Document report
*   Program source code, docker file, build file and/or any yaml
*   Program output file (Multiple samples to show performance)
*   Screenshots (If needed)

**Deadline:** Week 12 / 13 – See Animospace posted due date
