package pl.edu.agh.pawelkrucz;

import java.util.Arrays;

import org.apache.zookeeper.*;
import org.apache.zookeeper.AsyncCallback.StatCallback;
import org.apache.zookeeper.KeeperException.Code;
import org.apache.zookeeper.data.Stat;

public class DataMonitor implements Watcher, StatCallback {

    ZooKeeper zk;

    String znode;

    int numberOfDescendants;

    Watcher chainedWatcher;

    boolean dead;

    ExecutorProxy executorProxy;

    byte prevData[];

    public DataMonitor(ZooKeeper zk, String znode, Watcher chainedWatcher,
                       ExecutorProxy executorProxy) {
        this.zk = zk;
        this.znode = znode;
        this.chainedWatcher = chainedWatcher;
        this.executorProxy = executorProxy;
        // Get things started by checking if the node exists. We are going
        // to be completely event driven
        zk.exists(znode, true, this, null);
        this.numberOfDescendants = executorProxy.countDescendants(znode);
    }

    /**
     * Other classes use the DataMonitor by implementing this method
     */
    public interface ExecutorProxy {
        /**
         * The existence status of the node has changed.
         */
        void exists(byte data[]);

        void printChildren(String znode);

        int countDescendants(String znode);
        /**
         * The ZooKeeper session is no longer valid.
         *
         * @param rc
         *                the ZooKeeper reason code
         */
        void closing(int rc);
    }

    public void process(WatchedEvent event) {
        String path = event.getPath();
        if (event.getType() == Event.EventType.None) {
            // We are being told that the state of the
            // connection has changed
            switch (event.getState()) {
                case SyncConnected:
                    // In this particular example we don't need to do anything
                    // here - watches are automatically re-registered with
                    // server and any watches triggered while the client was
                    // disconnected will be delivered (in order of course)
                    break;
                case Expired:
                    // It's all over
                    dead = true;
                    executorProxy.closing(KeeperException.Code.SessionExpired);
                    break;
            }
        } else if (event.getType() == Event.EventType.NodeChildrenChanged) {
            executorProxy.printChildren(znode);
            int newNumberOfDescendants = executorProxy.countDescendants(znode);
            if (newNumberOfDescendants > this.numberOfDescendants){
                System.out.printf("Number of descendants of /z: %d%n", newNumberOfDescendants);
            }
            this.numberOfDescendants = newNumberOfDescendants;
        }else{
            if (path != null) {
                zk.exists(znode, true, this, null);

            }
        }
        if (chainedWatcher != null) {
            chainedWatcher.process(event);
        }
    }



    public void processResult(int rc, String path, Object ctx, Stat stat) {
        boolean exists;
        switch (rc) {
            case Code.Ok:
                exists = true;
                break;
            case Code.NoNode:
                exists = false;
                break;
            case Code.SessionExpired:
            case Code.NoAuth:
                dead = true;
                executorProxy.closing(rc);
                return;
            default:
                // Retry errors
                zk.exists(znode, true, this, null);
                return;
        }

        byte b[] = null;
        if (exists) {
            try {
                b = zk.getData(znode, false, null);
            } catch (KeeperException e) {
                // We don't need to worry about recovering now. The watch
                // callbacks will kick off any exception handling
                e.printStackTrace();
            } catch (InterruptedException e) {
                return;
            }
        }
        if ((b == null && b != prevData)
                || (b != null && !Arrays.equals(prevData, b))) {
            executorProxy.exists(b);
            prevData = b;
        }
    }
}