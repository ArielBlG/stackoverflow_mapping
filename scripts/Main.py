import javalang
import pandas as pd
import stackoverflow_java_queries
from CodeMapping import MapCreator
import json


def Main():
    # the query we send to bigquery datasset, joining question and answer by id
    # filter the limit to 10000 - need better computer for more
    questions_query = """
                        SELECT pq.title,pq.body, com.body as answers_body
    FROM `bigquery-public-data.stackoverflow.posts_questions` as pq
    inner join `bigquery-public-data.stackoverflow.posts_answers` as com on pq.id = com.parent_id
    WHERE pq.tags LIKE '%java%' AND pq.tags NOT LIKE '%javascript%' AND pq.body LIKE '%<code>%' AND pq.body LIKE '%class%' 
         AND com.body LIKE '%<code>%' AND com.body LIKE '%class%'
    LIMIT 10000
                      """

    """creates the datacollector"""

    # datacollector = stackoverflow_java_queries.dataCollector(r'Cred.json')
    # datacollector.openclient()
    # data_set = datacollector.getdataset(questions_query)  # get the data set created from the bigquery dataset
    # data_set.to_csv('df.csv')


    # data_set.to_csv('df2.csv')
    data_set = pd.read_csv('df2.csv', encoding="ISO-8859-1")

    codeextractor = stackoverflow_java_queries.codeExtractor(data_set)

    """optional -- recevie a csv file instead of panda df"""
    # codeextractor = codeExtractor(%PATH%)

    codes = codeextractor.extractCodes()

    """test a single code to map"""
    # list_codes = []
    code = """
    /** recursive dfs class */
    public class Dfs extends Recursive implements Search,GraphSeach {
    private int search_number;
    /** main function*/
    public static void main(String[] args) {
        int[][] arr = {
                // 1 2 3 4 5 6 7 8 9 10
                { 0, 1, 1, 1, 0, 0, 0, 0, 0, 0 }, // 1
                { 0, 0, 0, 0, 0, 0, 1, 0, 0, 0 }, // 2
                { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }, // 3
                { 0, 0, 0, 0, 1, 0, 0, 0, 0, 0 }, // 4
                { 0, 0, 0, 0, 0, 1, 0, 0, 0, 0 }, // 5
                { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }, // 6
                { 0, 0, 0, 0, 0, 0, 0, 1, 1, 0 }, // 7
                { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }, // 8
                { 0, 0, 0, 0, 0, 0, 0, 0, 0, 1 }, // 9
                { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 } // 10
        };
        boolean [] visited = new boolean[10];

        dfs(0, arr, visited);

    }
    /** recursive DFS function*/
    public static void dfs(int i, int[][] mat, boolean[] visited) {
        if(!visited[i]) {
            visited[i] = true; // Mark node as "visited"
            System.out.print( (i+1) + " ");

            for (int j = 0; j < mat[i].length; j++) {
                if (mat[i][j] == 1 && !visited[j]) {
                    dfs(j, mat, visited); // Visit node
                }
            }
        }
    }
}"""
    # parse the code
    # list_codes = []
    # list_codes.append(code)
    # code_dict = pd.DataFrame(columns=['title', 'text', 'code'])
    # df2 = pd.DataFrame([["dfs", "aaaaa", list_codes]], columns=['title', 'text', 'code'])
    # code_dict = pd.concat([df2, code_dict])


    codeparser = stackoverflow_java_queries.codeParser(codes)
    mapped_code = codeparser.parse_code()

    map_code = MapCreator.MapCreator(mapped_code)
    task_dict = map_code.create_dictionary()
    # print("done")
    with open("sample_1.json", 'w') as outfile:
        json.dump(task_dict[0], outfile)
    with open("sample_2.json", 'w') as outfile:
        json.dump(task_dict[1], outfile)


if __name__ == "__main__":
    Main()
