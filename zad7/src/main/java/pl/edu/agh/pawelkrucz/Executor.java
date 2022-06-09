package pl.edu.agh.pawelkrucz;

import java.io.*;
import java.util.List;

import org.apache.zookeeper.KeeperException;
import org.apache.zookeeper.WatchedEvent;
import org.apache.zookeeper.Watcher;
import org.apache.zookeeper.ZooKeeper;

public class Executor
        implements Watcher, Runnable, DataMonitor.ExecutorProxy
{
    private static final String ZNODE_NAME = "/z";
    private static final String HOST_PORT = "127.0.0.1:2181";

    DataMonitor dm;

    ZooKeeper zk;

    File file;

    Process child;

    public Executor(String filename) throws IOException {
        this.file = new File(filename);
        zk = new ZooKeeper(HOST_PORT, 3000, this);
        dm = new DataMonitor(zk, ZNODE_NAME, null, this);
    }

    /**
     * @param args
     */
    public static void main(String[] args) {
        if (args.length != 1) {
            System.err
                    .println("USAGE: Executor program");
            System.exit(2);
        }
        String filename = args[0];
        try {
            new Executor(filename).run();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void process(WatchedEvent event) {
        if (dm != null) {
            dm.process(event);
        }
    }

    public void run() {
        try {
            synchronized (this) {
                while (!dm.dead) {
                    wait();
                }
            }
        } catch (InterruptedException e) {
        }
    }

    public void closing(int rc) {
        synchronized (this) {
            notifyAll();
        }
    }

    public void exists(byte[] data) {
        if (data == null) {
            if (child != null) {
                System.out.println("Killing process");
                child.destroy();
                try {
                    child.waitFor();
                } catch (InterruptedException e) {
                }
            }
            child = null;
        } else {
            if (child != null) {
                System.out.println("Stopping child");
                child.destroy();
                try {
                    child.waitFor();
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
            try {
                System.out.println("Starting graphic program");
                child = Runtime.getRuntime().exec(file.getAbsolutePath());

                System.out.println("Current children of the node:");
                printChildren(ZNODE_NAME);

            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    public void printChildren(String znodeName) {
        try {
            List<String> children = zk.getChildren(znodeName, true);
            for (String childNode : children) {
                String fullChildName = znodeName + "/" + childNode;
                System.out.printf("%s%n", fullChildName);
                printChildren(fullChildName);
            }
        } catch (KeeperException | InterruptedException e){
            e.printStackTrace();
        }
    }

    public int countDescendants(String nodePath) {
        int result = 0;
        try {
            for (String childNode : zk.getChildren(nodePath, true)) {
                result += 1 + countDescendants(nodePath + "/" + childNode);
            }
        } catch (KeeperException e){
            return 0;
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        return result;
    }
}