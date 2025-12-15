import {
  Database,
  Edit,
  Eye,
  FileText,
  Globe,
  MessageSquare,
  Plus,
  Server,
  Trash2,
} from "lucide-react";
import React, { useEffect, useState } from "react";
import { apiService } from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import { activityLogger } from "../services/activityLogger";

interface DatabaseConfig {
  type: string;
  host: string;
  port: number;
  user?: string;
  username?: string;
  password: string;
  database: string;
  ssl: boolean;
  auth_source?: string;
}

interface DataChef {
  id: string;
  name: string;
  type: "csv" | "sql" | "nosql" | "api" | "messaging";
  path?: string;
  query?: string;
  url?: string;
  database?: string;
  collection?: string;
  brokers?: string;
  topic?: string;
  group_id?: string;
  rename_columns: string;
  status: "active" | "inactive" | "error";
  last_updated?: string;
  db_config?: DatabaseConfig;
}

const DataChefsPage: React.FC = () => {
  const { user } = useAuth();
  const [dataChefs, setDataChefs] = useState<DataChef[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedType, setSelectedType] = useState<string>("csv");
  const [selectedDataChef, setSelectedDataChef] = useState<DataChef | null>(
    null
  );
  const [formData, setFormData] = useState({
    dataChefId: "",
    filePath: "",
    query: "",
    database: "",
    collection: "",
    apiEndpoint: "",
    brokers: "",
    topic: "",
    groupId: "",
    renameColumns: "",
  });
  const [dbConfig, setDbConfig] = useState<DatabaseConfig>({
    type: "mysql",
    host: "",
    port: 3306,
    user: "",
    password: "",
    database: "",
    ssl: false,
    auth_source: "admin",
  });
  const [useCustomDb, setUseCustomDb] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  useEffect(() => {
    fetchDataChefs();
  }, []);

  const fetchDataChefs = async () => {
    try {
      const response = await apiService.listDataChefs();
      if (response.data) {
        // Backend returns object, convert to array
        const dataChefObject = response.data;
        const dataChefArray = Object.entries(dataChefObject).map(
          ([key, value]: [string, any]) => ({
            id: key,
            name: key,
            type: value.type,
            path: value.path,
            query: value.query,
            url: value.url,
            database: value.database,
            collection: value.collection,
            brokers: value.brokers,
            topic: value.topic,
            group_id: value.group_id,
            rename_columns: value.rename_columns || "",
            status: "active" as const,
            last_updated: new Date().toISOString(),
          })
        );
        setDataChefs(dataChefArray);
      }
    } catch (error) {
      console.error("Failed to fetch data chefs:", error);
      setDataChefs([]);
    } finally {
      setLoading(false);
    }
  };

  const handleEditDataChef = async (dataChef: DataChef) => {
    setSelectedDataChef(dataChef);
    setSelectedType(dataChef.type);
    setFormData({
      dataChefId: dataChef.id,
      filePath: dataChef.path || "",
      query: dataChef.query || "",
      database: dataChef.database || "",
      collection: dataChef.collection || "",
      apiEndpoint: dataChef.url || "",
      brokers: dataChef.brokers || "",
      topic: dataChef.topic || "",
      groupId: dataChef.group_id || "",
      renameColumns: dataChef.rename_columns || "",
    });

    if (dataChef.db_config) {
      setUseCustomDb(true);
      setDbConfig({
        type: dataChef.db_config.type || "mysql",
        host: dataChef.db_config.host || "",
        port: dataChef.db_config.port || 3306,
        user: dataChef.db_config.user || dataChef.db_config.username || "",
        password: dataChef.db_config.password || "",
        database: dataChef.db_config.database || "",
        ssl: dataChef.db_config.ssl || false,
        auth_source: dataChef.db_config.auth_source || "admin",
      });
    } else {
      setUseCustomDb(false);
      setDbConfig({
        type: "mysql",
        host: "",
        port: 3306,
        user: "",
        password: "",
        database: "",
        ssl: false,
        auth_source: "admin",
      });
    }

    setShowEditModal(true);
  };

  const handleUpdateDataChef = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDataChef) return;

    setIsUpdating(true);
    try {
      const updateData: Partial<DataChef> = {
        type: selectedType as any,
        rename_columns: formData.renameColumns,
      };

      // Add type-specific fields
      switch (selectedType) {
        case "csv":
          updateData.path = formData.filePath;
          break;
        case "sql":
          updateData.query = formData.query;
          if (useCustomDb) {
            const cleanDbConfig: any = {
              type: dbConfig.type,
              host: dbConfig.host,
              port: dbConfig.port,
              password: dbConfig.password,
              database: dbConfig.database,
              ssl: dbConfig.ssl,
            };

            if (dbConfig.type === "mongodb") {
              cleanDbConfig.username = dbConfig.user;
              cleanDbConfig.auth_source = dbConfig.auth_source;
            } else {
              cleanDbConfig.user = dbConfig.user;
            }

            updateData.db_config = cleanDbConfig;
          } else {
            updateData.db_config = null;
          }
          break;
        case "nosql":
          updateData.database = formData.database;
          updateData.collection = formData.collection;
          if (useCustomDb) {
            updateData.db_config = {
              type: dbConfig.type,
              host: dbConfig.host,
              port: dbConfig.port,
              username: dbConfig.user,
              password: dbConfig.password,
              database: dbConfig.database,
              ssl: dbConfig.ssl,
              auth_source: dbConfig.auth_source,
            };
          } else {
            updateData.db_config = null;
          }
          break;
        case "api":
          updateData.url = formData.apiEndpoint;
          break;
        case "messaging":
          updateData.brokers = formData.brokers;
          updateData.topic = formData.topic;
          updateData.group_id = formData.groupId;
          break;
      }

      const response = await apiService.editDataChef(
        selectedDataChef.id,
        updateData
      );

      if (response.error) {
        alert("Error: " + response.error);
      } else {
        alert("Data chef updated successfully!");

        if (user) {
          await activityLogger.log(user.id, user.email, {
            action: "update",
            resourceType: "data_chef",
            resourceId: selectedDataChef.id,
            details: {
              type: selectedType,
            },
          });
        }

        setShowEditModal(false);
        setSelectedDataChef(null);
        resetForm();
        fetchDataChefs();
      }
    } catch (error) {
      alert("Failed to update data chef");
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDeleteDataChef = async (dataChef: DataChef) => {
    if (
      window.confirm(
        `Are you sure you want to delete data chef "${dataChef.name}"?`
      )
    ) {
      try {
        const response = await apiService.deleteDataChef(dataChef.id);
        if (response.error) {
          alert("Error: " + response.error);
        } else {
          alert("Data chef deleted successfully!");

          if (user) {
            await activityLogger.log(user.id, user.email, {
              action: "delete",
              resourceType: "data_chef",
              resourceId: dataChef.id,
              details: {},
            });
          }

          fetchDataChefs();
        }
      } catch (error) {
        alert("Failed to delete data chef");
      }
    }
  };

  const handleViewDetails = async (dataChef: DataChef) => {
    try {
      const response = await apiService.getDataChef(dataChef.id);
      if (response.data) {
        setSelectedDataChef(response.data);
        setShowDetailsModal(true);
      } else {
        setSelectedDataChef(dataChef);
        setShowDetailsModal(true);
      }
    } catch (error) {
      console.error("Failed to fetch data chef details:", error);
      setSelectedDataChef(dataChef);
      setShowDetailsModal(true);
    }
  };

  const handleCreateDataChef = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);

    try {
      let response;
      const dbConfigToSend = useCustomDb ? dbConfig : undefined;

      switch (selectedType) {
        case "csv":
          if (selectedFile) {
            response = await apiService.uploadCsvFile(
              formData.dataChefId,
              selectedFile,
              formData.renameColumns
            );
          } else if (formData.filePath) {
            response = await apiService.createDataChefFromCsv(
              formData.dataChefId,
              formData.filePath,
              formData.renameColumns
            );
          } else {
            alert("Please select a file to upload or provide a file path");
            setIsCreating(false);
            return;
          }
          break;
        case "sql":
          response = await apiService.createDataChefFromSql(
            formData.dataChefId,
            formData.query,
            formData.renameColumns,
            dbConfigToSend
          );
          break;
        case "nosql":
          response = await apiService.createDataChefFromNoSql(
            formData.dataChefId,
            formData.database,
            formData.collection,
            formData.renameColumns,
            dbConfigToSend
          );
          break;
        case "api":
          response = await apiService.createDataChefFromApi(
            formData.dataChefId,
            formData.apiEndpoint,
            formData.renameColumns
          );
          break;
        case "messaging":
          response = await apiService.createDataChefFromMessageQueue(
            formData.dataChefId,
            formData.brokers,
            formData.topic,
            formData.renameColumns,
            formData.groupId
          );
          break;
        default:
          throw new Error("Unsupported data chef type");
      }

      if (response.error) {
        alert("Error: " + response.error);
      } else {
        alert("Data chef created successfully!");

        if (user) {
          await activityLogger.log(user.id, user.email, {
            action: "create",
            resourceType: "data_chef",
            resourceId: formData.dataChefId,
            details: {
              type: selectedType,
            },
          });
        }

        setShowCreateModal(false);
        resetForm();
        fetchDataChefs();
      }
    } catch (error) {
      alert("Failed to create data chef");
    } finally {
      setIsCreating(false);
    }
  };

  const resetForm = () => {
    setFormData({
      dataChefId: "",
      filePath: "",
      query: "",
      database: "",
      collection: "",
      apiEndpoint: "",
      brokers: "",
      topic: "",
      groupId: "",
      renameColumns: "",
    });
    setDbConfig({
      type: "mysql",
      host: "",
      port: 3306,
      user: "",
      password: "",
      database: "",
      ssl: false,
      auth_source: "admin",
    });
    setUseCustomDb(false);
    setSelectedType("csv");
    setSelectedFile(null);
    setUploadProgress(0);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "csv":
        return <FileText className="h-6 w-6" />;
      case "sql":
        return <Database className="h-6 w-6" />;
      case "nosql":
        return <Server className="h-6 w-6" />;
      case "api":
        return <Globe className="h-6 w-6" />;
      case "messaging":
        return <MessageSquare className="h-6 w-6" />;
      default:
        return <Database className="h-6 w-6" />;
    }
  };

  const getTypeDisplayName = (type: string) => {
    switch (type) {
      case "csv":
        return "CSV File";
      case "sql":
        return "SQL Database";
      case "nosql":
        return "NoSQL Database";
      case "api":
        return "REST API";
      case "messaging":
        return "Message Queue";
      default:
        return type.toUpperCase();
    }
  };

  const renderDatabaseConfigForm = () => (
    <div className="space-y-3 border border-base-300 rounded-lg p-4 bg-base-200/30">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-base-content">Database Configuration</h3>
        <label className="label cursor-pointer gap-2">
          <span className="label-text text-xs">Use Custom Database</span>
          <input
            type="checkbox"
            checked={useCustomDb}
            onChange={(e) => setUseCustomDb(e.target.checked)}
            className="checkbox checkbox-sm"
          />
        </label>
      </div>

      {useCustomDb && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">
                <span className="label-text text-xs">Database Type</span>
              </label>
              <select
                value={dbConfig.type}
                onChange={(e) =>
                  setDbConfig({ ...dbConfig, type: e.target.value, port: e.target.value === "mysql" ? 3306 : e.target.value === "postgresql" ? 5432 : 27017 })
                }
                className="select select-bordered select-sm w-full"
              >
                <option value="mysql">MySQL</option>
                <option value="postgresql">PostgreSQL</option>
                <option value="mongodb">MongoDB</option>
              </select>
            </div>
            <div>
              <label className="label">
                <span className="label-text text-xs">Port</span>
              </label>
              <input
                type="number"
                required={useCustomDb}
                value={dbConfig.port}
                onChange={(e) =>
                  setDbConfig({ ...dbConfig, port: parseInt(e.target.value) })
                }
                className="input input-bordered input-sm w-full"
                placeholder="3306"
              />
            </div>
          </div>

          <div>
            <label className="label">
              <span className="label-text text-xs">Host</span>
            </label>
            <input
              type="text"
              required={useCustomDb}
              value={dbConfig.host}
              onChange={(e) =>
                setDbConfig({ ...dbConfig, host: e.target.value })
              }
              className="input input-bordered input-sm w-full"
              placeholder="localhost or 192.168.1.100"
            />
          </div>

          <div>
            <label className="label">
              <span className="label-text text-xs">Database Name</span>
            </label>
            <input
              type="text"
              required={useCustomDb}
              value={dbConfig.database}
              onChange={(e) =>
                setDbConfig({ ...dbConfig, database: e.target.value })
              }
              className="input input-bordered input-sm w-full"
              placeholder="my_database"
            />
          </div>

          <div>
            <label className="label">
              <span className="label-text text-xs">Username</span>
            </label>
            <input
              type="text"
              required={useCustomDb}
              value={dbConfig.user || dbConfig.username || ""}
              onChange={(e) =>
                setDbConfig({ ...dbConfig, user: e.target.value, username: e.target.value })
              }
              className="input input-bordered input-sm w-full"
              placeholder="admin"
            />
          </div>

          <div>
            <label className="label">
              <span className="label-text text-xs">Password</span>
            </label>
            <input
              type="password"
              required={useCustomDb}
              value={dbConfig.password}
              onChange={(e) =>
                setDbConfig({ ...dbConfig, password: e.target.value })
              }
              className="input input-bordered input-sm w-full"
              placeholder="********"
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={dbConfig.ssl}
              onChange={(e) =>
                setDbConfig({ ...dbConfig, ssl: e.target.checked })
              }
              className="checkbox checkbox-sm"
            />
            <label className="label-text text-xs">Use SSL Connection</label>
          </div>

          <div className="alert alert-warning text-xs">
            <span>Database configuration will be stored securely. Sensitive information will be masked when viewing.</span>
          </div>
        </div>
      )}

      {!useCustomDb && (
        <div className="alert alert-info text-xs">
          <span>Using default database configuration from local.yaml</span>
        </div>
      )}
    </div>
  );

  const renderColumnMappingHelp = () => (
    <div>
      <label className="label">
        <span className="label-text font-semibold">Column Mapping (Required for Training)</span>
      </label>
      <input
        type="text"
        value={formData.renameColumns}
        onChange={(e) =>
          setFormData({ ...formData, renameColumns: e.target.value })
        }
        className="input input-bordered w-full"
        placeholder="userId->user_id,productId->item_id,rating->rating"
      />
      <div className="alert alert-info mt-2 text-xs">
        <div className="w-full">
          <div className="font-semibold mb-1">Required Columns for Model Training:</div>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li><strong>user_id</strong>: User identifier (string/number)</li>
            <li><strong>item_id</strong>: Item/Product identifier (string/number)</li>
            <li><strong>rating</strong>: Interaction score (number, optional - defaults to 1.0)</li>
          </ul>
          <div className="mt-2 pt-2 border-t border-info/30">
            <div className="font-semibold mb-1">Mapping Format:</div>
            <code className="bg-base-200 px-2 py-1 rounded">original_name-&gt;new_name,another_col-&gt;target_col</code>
            <div className="mt-1">Example: <code className="bg-base-200 px-2 py-1 rounded">userId-&gt;user_id,productId-&gt;item_id,clicks-&gt;rating</code></div>
          </div>
          <div className="mt-2 pt-2 border-t border-info/30">
            <div className="font-semibold mb-1">Tips for Different Sources:</div>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li><strong>CSV/Excel:</strong> Map your column names to required format</li>
              <li><strong>JSON API:</strong> Map JSON keys (e.g., "id-&gt;user_id,product-&gt;item_id")</li>
              <li><strong>SQL:</strong> Use aliases in query: <code className="bg-base-200 px-1 rounded">SELECT userId as user_id, productId as item_id</code></li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "badge-success";
      case "inactive":
        return "badge-ghost";
      case "error":
        return "badge-error";
      default:
        return "badge-ghost";
    }
  };

  const renderFormFields = () => {
    switch (selectedType) {
      case "csv":
        return (
          <div className="space-y-3">
            <div>
              <label className="label">
                <span className="label-text">File Upload</span>
              </label>
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    setSelectedFile(file);
                  }
                }}
                className="file-input file-input-bordered w-full"
              />
              {selectedFile && (
                <p className="text-xs text-success mt-1">
                  Selected: {selectedFile.name}
                </p>
              )}
            </div>
            <div className="divider text-xs">OR</div>
            <div>
              <label className="label">
                <span className="label-text">File Path (on server)</span>
              </label>
              <input
                type="text"
                value={formData.filePath}
                onChange={(e) =>
                  setFormData({ ...formData, filePath: e.target.value })
                }
                className="input input-bordered w-full"
                placeholder="/path/to/data.csv"
              />
              <p className="text-xs text-base-content/50 mt-1">
                Use this if file is already on the server
              </p>
            </div>
          </div>
        );
      case "sql":
        return (
          <div className="space-y-3">
            <div>
              <label className="label">
                <span className="label-text">SQL Query</span>
              </label>
              <textarea
                required
                value={formData.query}
                onChange={(e) =>
                  setFormData({ ...formData, query: e.target.value })
                }
                className="textarea textarea-bordered w-full"
                rows={3}
                placeholder="SELECT * FROM users WHERE..."
              />
            </div>
            {renderDatabaseConfigForm()}
          </div>
        );
      case "nosql":
        return (
          <div className="space-y-3">
            <div>
              <label className="label">
                <span className="label-text">Database Name</span>
              </label>
              <input
                type="text"
                required
                value={formData.database}
                onChange={(e) =>
                  setFormData({ ...formData, database: e.target.value })
                }
                className="input input-bordered w-full"
                placeholder="database_name"
              />
            </div>
            <div>
              <label className="label">
                <span className="label-text">Collection Name</span>
              </label>
              <input
                type="text"
                required
                value={formData.collection}
                onChange={(e) =>
                  setFormData({ ...formData, collection: e.target.value })
                }
                className="input input-bordered w-full"
                placeholder="collection_name"
              />
            </div>
            {renderDatabaseConfigForm()}
          </div>
        );
      case "api":
        return (
          <div>
            <label className="label">
              <span className="label-text">API Endpoint</span>
            </label>
            <input
              type="url"
              required
              value={formData.apiEndpoint}
              onChange={(e) =>
                setFormData({ ...formData, apiEndpoint: e.target.value })
              }
              className="input input-bordered w-full"
              placeholder="https://api.example.com/data"
            />
          </div>
        );
      case "messaging":
        return (
          <>
            <div>
              <label className="label">
                <span className="label-text">Brokers</span>
              </label>
              <input
                type="text"
                required
                value={formData.brokers}
                onChange={(e) =>
                  setFormData({ ...formData, brokers: e.target.value })
                }
                className="input input-bordered w-full"
                placeholder="broker1:9092,broker2:9092"
              />
            </div>
            <div>
              <label className="label">
                <span className="label-text">Topic</span>
              </label>
              <input
                type="text"
                required
                value={formData.topic}
                onChange={(e) =>
                  setFormData({ ...formData, topic: e.target.value })
                }
                className="input input-bordered w-full"
                placeholder="data_topic"
              />
            </div>
            <div>
              <label className="label">
                <span className="label-text">Group ID</span>
              </label>
              <input
                type="text"
                required
                value={formData.groupId}
                onChange={(e) =>
                  setFormData({ ...formData, groupId: e.target.value })
                }
                className="input input-bordered w-full"
                placeholder="data_group"
              />
            </div>
          </>
        );
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="text-center">
          <div className="loading loading-spinner loading-lg"></div>
          <p className="text-base-content/70 mt-4">Loading data chefs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-base-content mb-2">
            Data Chefs
          </h1>
          <p className="text-base-content/70">
            Manage your data sources and pipelines
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary gap-2"
        >
          <Plus className="h-5 w-5" />
          <span>Create Data Chef</span>
        </button>
      </div>

      {/* Data Chefs Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {dataChefs.map((chef) => (
          <div
            key={chef.id}
            className="card bg-base-100 shadow-sm hover:shadow-md transition-shadow duration-200"
          >
            <div className="card-body">
              <div className="flex items-center justify-between mb-4">
                <div className="bg-secondary/10 p-2 rounded-lg text-secondary">
                  {getTypeIcon(chef.type)}
                </div>
                {/* <div className={`badge ${getStatusColor(chef.status)}`}>
                  {chef.status}
                </div> */}
              </div>

              <h3 className="card-title text-base-content mb-2">{chef.name}</h3>
              <div className="space-y-2 mb-4">
                <p className="text-sm text-base-content/70">
                  Type:{" "}
                  <span className="font-medium">
                    {getTypeDisplayName(chef.type)}
                  </span>
                </p>
                {chef.path && (
                  <p className="text-sm text-base-content/70">
                    Path:{" "}
                    <span className="font-medium text-xs">{chef.path}</span>
                  </p>
                )}
                {chef.query && (
                  <p className="text-sm text-base-content/70">
                    Query:{" "}
                    <span className="font-medium text-xs">
                      {chef.query.substring(0, 30)}...
                    </span>
                  </p>
                )}
                {chef.url && (
                  <p className="text-sm text-base-content/70">
                    URL: <span className="font-medium text-xs">{chef.url}</span>
                  </p>
                )}
                {chef.rename_columns && (
                  <p className="text-sm text-base-content/70">
                    Column Mapping:{" "}
                    <span className="font-medium text-xs">
                      {chef.rename_columns}
                    </span>
                  </p>
                )}
                {chef.last_updated && (
                  <p className="text-sm text-base-content/70">
                    Last Updated:{" "}
                    <span className="font-medium">
                      {new Date(chef.last_updated).toLocaleDateString()}
                    </span>
                  </p>
                )}
              </div>

              <div className="card-actions justify-end">
                <button
                  onClick={() => handleViewDetails(chef)}
                  className="btn btn-info btn-sm gap-1"
                >
                  <Eye className="h-4 w-4" />
                  <span>Details</span>
                </button>
                <button
                  onClick={() => handleEditDataChef(chef)}
                  className="btn btn-warning btn-sm gap-1"
                >
                  <Edit className="h-4 w-4" />
                  <span>Edit</span>
                </button>
                <button
                  onClick={() => handleDeleteDataChef(chef)}
                  className="btn btn-error btn-sm"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {dataChefs.length === 0 && (
        <div className="text-center py-12">
          <Database className="h-12 w-12 text-base-content/40 mx-auto mb-4" />
          <p className="text-base-content/70 text-lg">No data chefs found</p>
          <p className="text-base-content/50 text-sm">
            Create your first data chef to get started
          </p>
        </div>
      )}

      {/* Data Chef Details Modal */}
      {showDetailsModal && selectedDataChef && (
        <div className="modal modal-open">
          <div className="modal-box max-w-2xl">
            <h2 className="text-xl font-bold text-base-content mb-4">
              Data Chef Details: {selectedDataChef.name}
            </h2>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">ID</span>
                  </label>
                  <p className="text-base-content">{selectedDataChef.id}</p>
                </div>
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">Type</span>
                  </label>
                  <div className="badge badge-primary">
                    {getTypeDisplayName(selectedDataChef.type)}
                  </div>
                </div>
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">Status</span>
                  </label>
                  <div
                    className={`badge ${getStatusColor(
                      selectedDataChef.status || "active"
                    )}`}
                  >
                    {selectedDataChef.status || "active"}
                  </div>
                </div>
                {selectedDataChef.last_updated && (
                  <div>
                    <label className="label">
                      <span className="label-text font-semibold">
                        Last Updated
                      </span>
                    </label>
                    <p className="text-base-content text-sm">
                      {new Date(selectedDataChef.last_updated).toLocaleString()}
                    </p>
                  </div>
                )}
              </div>

              {/* Type-specific details */}
              {selectedDataChef.path && (
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">File Path</span>
                  </label>
                  <div className="bg-base-200 p-3 rounded-lg">
                    <code className="text-sm">{selectedDataChef.path}</code>
                  </div>
                </div>
              )}

              {selectedDataChef.query && (
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">SQL Query</span>
                  </label>
                  <div className="bg-base-200 p-3 rounded-lg">
                    <code className="text-sm whitespace-pre-wrap">
                      {selectedDataChef.query}
                    </code>
                  </div>
                </div>
              )}

              {selectedDataChef.url && (
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">API URL</span>
                  </label>
                  <div className="bg-base-200 p-3 rounded-lg">
                    <code className="text-sm">{selectedDataChef.url}</code>
                  </div>
                </div>
              )}

              {(selectedDataChef.database || selectedDataChef.collection) && (
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">
                      NoSQL Configuration
                    </span>
                  </label>
                  <div className="bg-base-200 p-3 rounded-lg space-y-1">
                    {selectedDataChef.database && (
                      <div>
                        <strong>Database:</strong> {selectedDataChef.database}
                      </div>
                    )}
                    {selectedDataChef.collection && (
                      <div>
                        <strong>Collection:</strong>{" "}
                        {selectedDataChef.collection}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {(selectedDataChef.brokers || selectedDataChef.topic) && (
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">
                      Messaging Configuration
                    </span>
                  </label>
                  <div className="bg-base-200 p-3 rounded-lg space-y-1">
                    {selectedDataChef.brokers && (
                      <div>
                        <strong>Brokers:</strong> {selectedDataChef.brokers}
                      </div>
                    )}
                    {selectedDataChef.topic && (
                      <div>
                        <strong>Topic:</strong> {selectedDataChef.topic}
                      </div>
                    )}
                    {selectedDataChef.group_id && (
                      <div>
                        <strong>Group ID:</strong> {selectedDataChef.group_id}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {selectedDataChef.rename_columns && (
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">
                      Column Mapping
                    </span>
                  </label>
                  <div className="bg-base-200 p-3 rounded-lg">
                    <code className="text-sm">
                      {selectedDataChef.rename_columns}
                    </code>
                  </div>
                </div>
              )}

              {selectedDataChef.db_config && (
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">
                      Database Configuration
                    </span>
                  </label>
                  <div className="bg-base-200 p-3 rounded-lg space-y-2 text-sm">
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <strong>Type:</strong> {selectedDataChef.db_config.type}
                      </div>
                      <div>
                        <strong>Port:</strong> {selectedDataChef.db_config.port}
                      </div>
                    </div>
                    <div>
                      <strong>Host:</strong>{" "}
                      <span className="text-warning">
                        {selectedDataChef.db_config.host}
                      </span>
                    </div>
                    <div>
                      <strong>Database:</strong>{" "}
                      {selectedDataChef.db_config.database}
                    </div>
                    <div>
                      <strong>Username:</strong>{" "}
                      <span className="text-warning">
                        {selectedDataChef.db_config.user || selectedDataChef.db_config.username}
                      </span>
                    </div>
                    <div>
                      <strong>Password:</strong>{" "}
                      <span className="text-error">
                        {selectedDataChef.db_config.password}
                      </span>
                    </div>
                    <div>
                      <strong>SSL:</strong>{" "}
                      {selectedDataChef.db_config.ssl ? "Enabled" : "Disabled"}
                    </div>
                    <div className="alert alert-warning text-xs mt-2">
                      <span>Sensitive values (host, username, password) are masked for security</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="modal-action">
              <button
                onClick={() => setShowDetailsModal(false)}
                className="btn btn-ghost"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Data Chef Modal */}
      {showEditModal && selectedDataChef && (
        <div className="modal modal-open">
          <div className="modal-box max-w-md max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-base-content mb-4">
              Edit Data Chef: {selectedDataChef.name}
            </h2>
            <form onSubmit={handleUpdateDataChef} className="space-y-4">
              <div>
                <label className="label">
                  <span className="label-text">Data Chef ID</span>
                </label>
                <input
                  type="text"
                  disabled
                  value={formData.dataChefId}
                  className="input input-bordered w-full input-disabled"
                />
              </div>

              <div>
                <label className="label">
                  <span className="label-text">Data Source Type</span>
                </label>
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="select select-bordered w-full"
                >
                  <option value="csv">CSV File</option>
                  <option value="sql">SQL Database</option>
                  <option value="nosql">NoSQL Database</option>
                  <option value="api">REST API</option>
                  <option value="messaging">Message Queue</option>
                </select>
              </div>

              {renderFormFields()}

              {renderColumnMappingHelp()}

              <div className="modal-action">
                <button
                  type="submit"
                  disabled={isUpdating}
                  className="btn btn-primary"
                >
                  {isUpdating ? "Updating..." : "Update Data Chef"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false);
                    setSelectedDataChef(null);
                    resetForm();
                  }}
                  className="btn btn-ghost"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Data Chef Modal */}
      {showCreateModal && (
        <div className="modal modal-open">
          <div className="modal-box max-w-md max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-base-content mb-4">
              Create New Data Chef
            </h2>
            <form onSubmit={handleCreateDataChef} className="space-y-4">
              <div>
                <label className="label">
                  <span className="label-text">Data Chef ID</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.dataChefId}
                  onChange={(e) =>
                    setFormData({ ...formData, dataChefId: e.target.value })
                  }
                  className="input input-bordered w-full"
                  placeholder="my_data_chef"
                />
              </div>

              <div>
                <label className="label">
                  <span className="label-text">Data Source Type</span>
                </label>
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="select select-bordered w-full"
                >
                  <option value="csv">CSV File</option>
                  <option value="sql">SQL Database</option>
                  <option value="nosql">NoSQL Database</option>
                  <option value="api">REST API</option>
                  <option value="messaging">Message Queue</option>
                </select>
              </div>

              {renderFormFields()}

              {renderColumnMappingHelp()}

              <div className="modal-action">
                <button
                  type="submit"
                  disabled={isCreating}
                  className="btn btn-primary"
                >
                  {isCreating ? "Creating..." : "Create Data Chef"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    resetForm();
                  }}
                  className="btn btn-ghost"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataChefsPage;
