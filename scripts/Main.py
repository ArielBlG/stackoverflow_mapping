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
    # data_set = pd.read_csv('df2.csv', encoding="ISO-8859-1")

    # codeextractor = stackoverflow_java_queries.codeExtractor(data_set)

    """optional -- recevie a csv file instead of panda df"""
    # codeextractor = codeExtractor(%PATH%)

    # codes = codeextractor.extractCodes()

    """test a single code to map"""
    code = """import java.io.*;
import java.util.*;
//try
interface dataStructure{

}
/** code search for the graph */
class Search{
    public void activate_search(String search_name, Graph g, int v){
        if(search_name.equals("DFS")){
            DFS dfs = new DFS();
            dfs.DFS(v,g);
        }
    }
}
class DFS extends Search{
    static Graph graph;
    /**A function used by DFS */
    void DFSUtil(int v,boolean visited[])

    {
        visited[v] = true;
        System.out.print(v+" ");

        Iterator<Integer> i = graph.adj[v].listIterator();
        while (i.hasNext())
        {
            int n = i.next();
            if (!visited[n])
                DFSUtil(n, visited);
        }
    }

    /**The function to do DFS traversal. It uses recursive DFSUtil() */
    void DFS(int v, Graph g)
    {
        graph = g;
        boolean visited[] = new boolean[g.getV()];

        DFSUtil(v, visited);
    }
}
public class Graph implements dataStructure{
    private int V;
    public LinkedList<Integer> adj[];

    public LinkedList<Integer>[] get_adj(){
        return this.adj;
    }
    public int getV(){
        return this.V;
    }
    /** constructor*/
    Graph(int v)
    {
        V = v;
        adj = new LinkedList[v];
        for (int i=0; i<v; ++i)
            adj[i] = new LinkedList();
    }

    /**Function to add an edge into the graph*/
    void addEdge(int v, int w)
    {
        adj[v].add(w);  // Add w to v's list.
    }


    /** main class */
    public static void main(String[] args) {
        Graph g = new Graph(4);

        g.addEdge(0, 1);
        g.addEdge(0, 2);
        g.addEdge(1, 2);
        g.addEdge(2, 0);
        g.addEdge(2, 3);
        g.addEdge(3, 3);

        System.out.println("Following is Depth First Traversal "+
                "(starting from vertex 2)");

        Search search = new Search();
        search.activate_search("DFS", g,2);
    }
}
"""
    # parse the code
    list_codes = []
    list_codes.append(code)
    code_dict = pd.DataFrame(columns=['title', 'text', 'code'])
    df2 = pd.DataFrame([["Recursive DFS implementation java", "implementation of DFS including graph", list_codes]], columns=['title', 'text', 'code'])
    code_dict = pd.concat([df2, code_dict])


    codeparser = stackoverflow_java_queries.codeParser(code_dict)
    # codeparser = stackoverflow_java_queries.codeParser(codes)
    mapped_code = codeparser.parse_code()

    map_code = MapCreator.MapCreator(mapped_code)
    task_dict = map_code.create_dictionary()
    print("done")
    with open("sample_1.json", 'w') as outfile:
        json.dump(task_dict[0], outfile)
    # with open("sample_2.json", 'w') as outfile:
    #     json.dump(task_dict[1], outfile)


if __name__ == "__main__":
    Main()
