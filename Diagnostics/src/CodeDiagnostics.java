import java.io.BufferedReader;
import java.io.IOException;
import java.io.StringReader;
import java.util.*;

import javax.tools.Diagnostic;
import javax.tools.DiagnosticCollector;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.ToolProvider;
import java.lang.UnsupportedOperationException;

public class CodeDiagnostics {

    public static void main(String[] args) throws IOException {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();

        StandardJavaFileManager fileManager = compiler.getStandardFileManager(null, null, null);
        Iterable<? extends JavaFileObject> compilationUnits =
                fileManager.getJavaFileObjectsFromStrings(Arrays.asList("/Users/ariel-pc/Desktop/test_code.java"));

        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<JavaFileObject>();

        compiler.getTask(null, fileManager, diagnostics, null, null, compilationUnits).call();

        StringBuilder reporter = new StringBuilder("");
        System.out.println(CodeDiagnostics.check(diagnostics));
        generateDiagnosticReport(diagnostics, reporter);
        System.out.println(reporter);
        throw new java.lang.UnsupportedOperationException("... error");
    }

    public static List<String> check(DiagnosticCollector<JavaFileObject> diagnostics /**String file*/) {
//        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
//
//        StandardJavaFileManager fileManager = compiler.getStandardFileManager(null, null, null);
//        Iterable<? extends JavaFileObject> compilationUnits =
//                fileManager.getJavaFileObjectsFromStrings(Arrays.asList(file));
//
//        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<JavaFileObject>();
//        compiler.getTask(null, fileManager, diagnostics, null, null, compilationUnits).call();

        List<String> messages = new ArrayList<String>();
        Formatter formatter = new Formatter();
        for (Diagnostic diagnostic : diagnostics.getDiagnostics()) {
            messages.add(diagnostic.getKind() + ":\t Line [" + diagnostic.getLineNumber() + "] \t Position [" + diagnostic.getPosition() + "]\t" + diagnostic.getMessage(Locale.ROOT) + "\n");
        }

        return messages;
    }

    private static void generateDiagnosticReport(
            DiagnosticCollector<JavaFileObject> collector, StringBuilder reporter) throws IOException {
        List<Diagnostic<? extends JavaFileObject>> diagnostics = collector.getDiagnostics();
        for (Diagnostic<? extends JavaFileObject> diagnostic : diagnostics) {
            JavaFileObject source = diagnostic.getSource();
            if (source != null) {
                reporter.append("Source: ").append(source.getName()).append('\n');
                reporter.append("Line ").append(diagnostic.getLineNumber()).append(": ")
                        .append(diagnostic.getMessage(Locale.ENGLISH)).append('\n');
                CharSequence content = source.getCharContent(true);
                BufferedReader reader = new BufferedReader(new StringReader(content.toString()));
                int i = 1;
                String line;
                while ((line = reader.readLine()) != null) {
                    reporter.append(i).append('\t').append(line).append('\n');
                    ++i;
                }
            } else {
                reporter.append("Source: (null)\n");
                reporter.append("Line ").append(diagnostic.getLineNumber()).append(": ")
                        .append(diagnostic.getMessage(Locale.ENGLISH)).append('\n');
            }
            reporter.append('\n');
        }
    }
}
